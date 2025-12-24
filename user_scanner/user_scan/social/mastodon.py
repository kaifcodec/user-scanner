import re
from user_scanner.core.orchestrator import status_validate
from user_scanner.core.result import Result


def validate_mastodon(user: str) -> Result:
    if not (3 <= len(user) <= 30):
        return Result.error("Length must be 3-30 characters")

    if not re.match(r'^[a-zA-Z0-9_-]+$', user):
        return Result.error("Usernames can only contain letters, numbers, underscores and hyphens")

    if not re.match(r'^[a-zA-Z0-9].*[a-zA-Z0-9]$', user):
        return Result.error("Username must start and end with a letter or number")

    url = f"https://mastodon.social/api/v1/accounts/lookup?acct={user}"

    return status_validate(url, 404, 200, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_mastodon(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
