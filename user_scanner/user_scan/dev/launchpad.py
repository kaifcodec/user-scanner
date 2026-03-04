from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import status_validate


def validate_launchpad(user):
    url = f"https://launchpad.net/~{user}"
    show_url = f"https://launchpad.net/~{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Upgrade-Insecure-Requests": "1",
    }

    return status_validate(
        url, 404, 200, show_url=show_url, headers=headers, follow_redirects=True
    )
