import html
import re
from urllib.parse import quote
from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.orchestrator import Result


def validate_gamebanana(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://gamebanana.com/members/{safe_user}"
    show_url = f"https://gamebanana.com/members/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            if "ErrorDocument" in response.text or "The member you are looking for does not exist" in response.text or "Member Not Found" in response.text:
                return Result.available(url=show_url)
            extra: dict[str, object] = {}
            media = {}
            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE)
            if title_match:
                title = html.unescape(title_match.group(1).replace("[GameBanana]", "").strip())
                if title:
                    extra["title"] = title
            img_match = re.search(
                r"""<meta[^>]*property=["']og:image["'][^>]*content=["']([^"']+)["']""",
                response.text,
                re.IGNORECASE,
            )
            if img_match and "default" not in img_match.group(1).lower():
                media["avatar"] = img_match.group(1).strip()
            desc_match = re.search(
                r"""<meta[^>]*property=["']og:description["'][^>]*content=["']([^"']+)["']""",
                response.text,
                re.IGNORECASE,
            )
            if desc_match:
                desc = html.unescape(desc_match.group(1).strip())
                if desc:
                    extra["bio"] = desc
            return Result.taken(extra=extra if extra else None, media=media if media else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return impersonate_validate(url, process, show_url=show_url)
