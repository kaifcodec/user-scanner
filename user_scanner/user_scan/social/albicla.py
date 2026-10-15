import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_albicla(user: str) -> Result:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,50}", user):
        return Result.error("Invalid username format")

    url = f"https://albicla.com/{user}"
    show_url = f"https://albicla.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
    }

    def process(response):
        if response.status_code == 404 and (
            "nie ma takiej strony" in response.text.lower()
        ):
            return Result.available()

        if response.status_code == 200 and (
            "document.location.href='/login'" in response.text
            or 'document.location.href="/login"' in response.text
        ):
            return Result.taken()

        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers, follow_redirects=False)
