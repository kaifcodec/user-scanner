import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, status_validate


def validate_leetcode(user: str) -> Result:
    if not (3 <= len(user) <= 30):
        return Result.error("Length must be between 3 and 30 characters")

    if not re.match(r"^[a-zA-Z0-9._-]+$", user):
        return Result.error(
            "Can only use letters, numbers, underscores, periods, or hyphens"
        )

    url = f"https://leetcode.com/u/{user}/"
    show_url = f"https://leetcode.com/u/{user}/"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "identity",
        "upgrade-insecure-requests": "1",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=0, i",
    }

    return status_validate(
        url, 404, 200, show_url=show_url, headers=headers, follow_redirects=True
    )
