import re
from user_scanner.core.orchestrator import status_validate
from user_scanner.core.result import Result


def validate_lemmy(user: str) -> Result:
    """Check username availability on Lemmy (lemmy.world instance)"""

    # Lemmy username rules: 3-20 chars, alphanumeric and underscores only
    if not (3 <= len(user) <= 20):
        return Result.error("Length must be 3-20 characters")

    if not re.match(r'^[a-zA-Z0-9_]+$', user):
        return Result.error("Only letters, numbers, and underscores allowed")

    url = f"https://lemmy.world/api/v3/user?username={user}"

    return status_validate(url, [400, 404], 200, timeout=5.0)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_lemmy(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
