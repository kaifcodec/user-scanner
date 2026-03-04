import re

from user_scanner.core.orchestrator import Result, generic_validate


def validate_lichess(user: str) -> Result:
    if not (2 <= len(user) <= 20):
        return Result.error("Length must be 2-20 characters")

    if not re.match(r"^[a-zA-Z0-9_-]+$", user):
        return Result.error(
            "Usernames can only contain letters, numbers, underscores, and hyphens"
        )

    if re.search(r"[_-]{2,}", user):
        return Result.error(
            "Username cannot contain consecutive underscores or hyphens"
        )

    if not re.match(r".*[a-zA-Z0-9]$", user):
        return Result.error("Username must end with a letter or a number")

    url = f"https://lichess.org/api/player/autocomplete?term={user}&exists=1"
    show_url = f"https://lichess.org/@/{user}"

    def process(response):
        res_text = response.text.strip().lower()
        if res_text == "true":
            return Result.taken()
        if res_text == "false":
            return Result.available()
        return Result.error("Unexpected error, report it via github issues")

    return generic_validate(url, process, show_url=show_url, timeout=3.0)
