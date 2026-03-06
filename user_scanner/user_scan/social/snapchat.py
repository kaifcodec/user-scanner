from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import status_validate


def validate_snapchat(user):
    url = f"https://www.snapchat.com/@{user}"
    show_url = f"https://www.snapchat.com/@{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "upgrade-insecure-requests": "1",
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=0, i",
    }

    return status_validate(
        url, 404, 200, show_url=show_url, headers=headers, follow_redirects=True
    )
