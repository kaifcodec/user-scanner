import re
from user_scanner.core.orchestrator import status_validate, Result


def validate_sourceforge(user: str) -> Result:
    if not (3 <= len(user) <= 30):
        return Result.error("Length must be 3-30 characters.")

    if not re.match(r'^[a-z0-9-]+$', user):

        if re.search(r'[A-Z]', user):
            return Result.error("Use lowercase letters only.")

        return Result.error("Only use lowercase letters, numbers, and dashes.")

    url = f"https://sourceforge.net/u/{user}/"

    return status_validate(url, 404, 200, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_sourceforge(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
