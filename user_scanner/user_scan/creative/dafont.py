import html
import re
from user_scanner.core.orchestrator import Result, generic_validate


def validate_dafont(user: str) -> Result:
    url = "https://www.dafont.com/profile.php"
    show_url = f"https://www.dafont.com/profile.php?user={user}"
    params = {"user": user}

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, object] = {}
            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
                if title and "error 404" not in title.lower():
                    extra["title"] = " ".join(title.split())
                    return Result.taken(extra=extra, url=show_url)
            return Result.available(url=show_url)
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
