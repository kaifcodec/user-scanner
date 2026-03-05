import re

from user_scanner.core.orchestrator import Result, status_validate


def validate_gumroad(user: str) -> Result:
    if not re.fullmatch(r"[a-z0-9]{3,20}", user):
        return Result.error(
            "Username must be between 3 and 20 lowercase alphanumeric characters"
        )

    url = f"https://{user}.gumroad.com/"
    show_url = f"https://{user}.gumroad.com"
    return status_validate(url, 404, 200, show_url=show_url, follow_redirects=True)
