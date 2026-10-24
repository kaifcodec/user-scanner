import html
import re
from urllib.parse import quote
from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.orchestrator import Result


def validate_flipboard(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://flipboard.com/@{safe_user}"
    show_url = f"https://flipboard.com/@{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, object] = {}
            media = {}

            # Title
            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
                if title:
                    extra["title"] = " ".join(title.split())

            # OpenGraph / Twitter Image (Avatar)
            img_match = re.search(
                r"""<(?:meta|link)[^>]*(?:property=["']og:image["']|name=["'](?:twitter:image|twitter:image:src)["'])[^>]*content=["']([^"']+)["']""",
                response.text,
                re.IGNORECASE,
            )
            if img_match:
                img_url = img_match.group(1).strip()
                if img_url and not any(k in img_url.lower() for k in ("default", "logo", "placeholder", "blank")):
                    media["avatar"] = img_url

            # OpenGraph / Twitter Description (Bio)
            desc_match = re.search(
                r"""<meta[^>]*(?:property=["']og:description["']|name=["'](?:description|twitter:description)["'])[^>]*content=["']([^"']+)["']""",
                response.text,
                re.IGNORECASE,
            )
            if desc_match:
                desc = html.unescape(desc_match.group(1).strip())
                if desc and not any(k in desc.lower() for k in ("404", "not found", "error", "sign up", "log in")):
                    extra["bio"] = " ".join(desc.split())

            # OpenGraph Title / Display Name
            name_match = re.search(
                r"""<meta[^>]*(?:property=["']og:title["']|name=["']twitter:title["'])[^>]*content=["']([^"']+)["']""",
                response.text,
                re.IGNORECASE,
            )
            if name_match:
                raw_name = html.unescape(name_match.group(1).strip())
                if raw_name and raw_name != extra.get("title"):
                    extra["name"] = " ".join(raw_name.split())

            return Result.taken(extra=extra if extra else None, media=media if media else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return impersonate_validate(url, process, show_url=show_url, allow_redirects=True)
