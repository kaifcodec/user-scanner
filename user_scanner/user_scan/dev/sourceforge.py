import re

from user_scanner.core.orchestrator import Result, status_validate


def validate_sourceforge(user: str) -> Result:
    if not (3 <= len(user) <= 30):
        return Result.error("Length must be 3-30 characters.")

    if not re.match(r"^[a-z0-9-]+$", user):
        if re.search(r"[A-Z]", user):
            return Result.error("Use lowercase letters only.")

        return Result.error("Only use lowercase letters, numbers, and dashes.")

    url = f"https://sourceforge.net/u/{user}/"
    show_url = f"https://sourceforge.net/u/{user}/"

    return status_validate(url, 404, 200, show_url=show_url, follow_redirects=True)
