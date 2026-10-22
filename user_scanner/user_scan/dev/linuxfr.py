import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_linuxfr(user: str) -> Result:
    url = f"https://linuxfr.org/users/{user}"
    show_url = f"https://linuxfr.org/users/{user}"
    headers = {"User-Agent": get_random_user_agent()}

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

    return generic_validate(url, process, show_url=show_url, headers=headers, follow_redirects=True)
