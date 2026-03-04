import re

from user_scanner.core.orchestrator import Result, status_validate


def validate_bitbucket(user: str) -> Result:
    if not (1 <= len(user) <= 30):
        return Result.error("Length must be 1-30 characters.")

    if not re.match(r"^[a-z0-9][a-z0-9_-]*$", user):
        if re.search(r"[A-Z]", user):
            return Result.error("Use lowercase letters only.")

        return Result.error(
            "Only use lowercase letters, numbers, hyphens, and underscores."
        )

    url = f"https://bitbucket.org/{user}/"
    show_url = f"https://bitbucket.org/{user}/"

    return status_validate(
        url, 404, [200, 302], show_url=show_url, follow_redirects=True
    )
