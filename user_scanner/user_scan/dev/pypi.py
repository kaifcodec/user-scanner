import re

from user_scanner.core.orchestrator import Result, status_validate


def validate_pypi(user):
    if not re.match(r"^(?!_+$)[A-Za-z0-9._-]+$", user):
        return Result.error(
            "Username may only contain letters, numbers, periods, underscores, and hyphens, and cannot consist solely of underscores"
        )

    url = f"https://pypi.org/user/{user}"
    show_url = f"https://pypi.org/{user}"

    return status_validate(
        url, 404, 200, show_url=show_url, timeout=3.0, follow_redirects=False
    )
