import re

from user_scanner.core.orchestrator import status_validate
from user_scanner.core.result import Result


def validate_lemmy(user: str) -> Result:
    """Check username availability on Lemmy (lemmy.world instance)"""

    # Lemmy username rules: 3-20 chars, alphanumeric and underscores only
    if not (3 <= len(user) <= 20):
        return Result.error("Length must be 3-20 characters")

    if not re.match(r"^[a-zA-Z0-9_]+$", user):
        return Result.error("Only letters, numbers, and underscores allowed")

    url = f"https://lemmy.world/api/v3/user?username={user}"
    show_url = f"https://lemmy.world/u/{user}"

    return status_validate(url, [400, 404], 200, show_url=show_url, timeout=5.0)
