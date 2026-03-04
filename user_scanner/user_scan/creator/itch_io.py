import re

from user_scanner.core.orchestrator import Result, status_validate


def validate_itch_io(user: str) -> Result:
    if not (2 <= len(user) <= 25):
        return Result.error("Length must be 2-25 characters.")

    if not re.match(r"^[a-z0-9_-]+$", user):
        if re.search(r"[A-Z]", user):
            return Result.error("Use lowercase letters only.")

        return Result.error(
            "Only use lowercase letters, numbers, underscores, and hyphens."
        )

    url = f"https://itch.io/profile/{user}"
    show_url = f"https://itch.io/profile/{user}"

    return status_validate(url, 404, 200, show_url=show_url, follow_redirects=True)
