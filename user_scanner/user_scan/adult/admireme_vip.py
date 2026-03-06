from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_admireme_vip(user):
    url = f"https://admireme.vip/{user}/"
    show_url = f"https://admireme.vip/{user}/"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response):
        if "creator-stat subscriber" in response.text:
            return Result.taken()

        if response.status_code == 404 or "<title>Page Not Found |" in response.text:
            return Result.available()

        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
