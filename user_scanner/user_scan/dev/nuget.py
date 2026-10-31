import html
import re
from urllib.parse import quote
from user_scanner.core.orchestrator import Result, generic_validate


def validate_nuget(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://www.nuget.org/profiles/{safe_user}"
    show_url = f"https://www.nuget.org/profiles/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, object] = {}
            media = {}
            media["avatar"] = f"https://www.nuget.org/profiles/{safe_user}/avatar?imageSize=512"

            pkg_match = re.search(r'<div class="value">(\d+)</div>\s*<div class="description">Packages</div>', response.text)
            if pkg_match:
                extra["packages"] = int(pkg_match.group(1))

            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
                if title:
                    extra["title"] = " ".join(title.split())
            return Result.taken(extra=extra if extra else None, media=media, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
