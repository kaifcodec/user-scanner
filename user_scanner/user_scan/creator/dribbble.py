from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import status_validate


def validate_dribbble(user):
    url = f"https://dribbble.com/{user}"
    show_url = f"https://dribbble.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
    }

    return status_validate(url, 404, 200, show_url=show_url, headers=headers)
