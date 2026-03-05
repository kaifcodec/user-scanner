from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import status_validate


def validate_cratesio(user):
    url = f"https://crates.io/api/v1/users/{user}"
    show_url = f"https://crates.io/users/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
        "Referer": "https://crates.io/",
        "sec-fetch-mode": "cors",
    }

    return status_validate(url, 404, 200, show_url=show_url, headers=headers)
