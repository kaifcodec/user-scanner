import re
from user_scanner.core.orchestrator import status_validate, Result


def validate_itch_io(user: str) -> Result:
    if not (2 <= len(user) <= 25):
        return Result.error("Length must be 2-25 characters.")

    if not re.match(r'^[a-z0-9_-]+$', user):

        if re.search(r'[A-Z]', user):
            return Result.error("Use lowercase letters only.")

        return Result.error("Only use lowercase letters, numbers, underscores, and hyphens.")

    url = f"https://itch.io/profile/{user}"

    return status_validate(url, 404, 200, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_itch_io(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
