import re
from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.orchestrator import Result


def validate_gamebanana(user: str) -> Result:
    url = f"https://gamebanana.com/members/{user}"
    show_url = url

    def process(response) -> Result:
        if response.status_code == 200:
            if "ErrorDocument" in response.text or "The member you are looking for does not exist" in response.text or "Member Not Found" in response.text:
                return Result.available(url=show_url)
            extra = {}
            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).replace("[GameBanana]", "").strip()
                if title:
                    extra["title"] = title
            return Result.taken(extra=extra if extra else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return impersonate_validate(url, process, show_url=show_url)
