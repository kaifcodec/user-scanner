import html
import re
from urllib.parse import quote
from user_scanner.core.orchestrator import Result, generic_validate


def validate_jeuxvideo(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://www.jeuxvideo.com/profil/{safe_user}"
    show_url = f"https://www.jeuxvideo.com/profil/{user}?mode=infos"
    params = {"mode": "infos"}

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, object] = {}
            media = {}
            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
                if title:
                    extra["title"] = " ".join(title.split())
            img_match = re.search(
                r"""<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']""",
                response.text,
                re.IGNORECASE,
            )
            if img_match and "default" not in img_match.group(1).lower():
                media["avatar"] = img_match.group(1).strip()
            return Result.taken(extra=extra if extra else None, media=media if media else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return generic_validate(
        url,
        process,
        show_url=show_url,
        params=params,
        follow_redirects=True,
    )
