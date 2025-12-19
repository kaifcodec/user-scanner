import re
from user_scanner.core.orchestrator import generic_validate, Result


def validate_lichess(user: str) -> Result:
    if not (2 <= len(user) <= 20):
        return Result.error("Length must be 2-20 characters")

    if not re.match(r'^[a-zA-Z0-9_-]+$', user):
        return Result.error("Usernames can only contain letters, numbers, underscores, and hyphens")

    if re.search(r'[_-]{2,}', user):
        return Result.error("Username cannot contain consecutive underscores or hyphens")

    if not re.match(r'.*[a-zA-Z0-9]$', user):
        return Result.error("Username must end with a letter or a number")

    url = f"https://lichess.org/api/player/autocomplete?term={user}&exists=1"

    def process(response):
        res_text = response.text.strip().lower()
        if res_text == "true":
            return Result.taken()
        if res_text == "false":
            return Result.available()
        return Result.error("Unexpected error, report it via github issues")

    return generic_validate(url, process, timeout=3.0)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_lichess(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
