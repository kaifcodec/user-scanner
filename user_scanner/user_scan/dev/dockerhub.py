from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import status_validate


def validate_dockerhub(user):
    url = f"https://hub.docker.com/v2/users/{user}/"
    show_url = f"https://hub.docker.com/u/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    return status_validate(url, 404, 200, show_url=show_url, headers=headers)
