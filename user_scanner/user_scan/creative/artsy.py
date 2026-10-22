import re
from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.orchestrator import Result


def validate_artsy(user: str) -> Result:
    url = f"https://www.artsy.net/artist/{user}"
    show_url = f"https://www.artsy.net/artist/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            extra = {}
            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                if title:
                    extra["title"] = " ".join(title.split())
            return Result.taken(extra=extra if extra else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return impersonate_validate(url, process, show_url=show_url, allow_redirects=True)
