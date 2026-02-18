import re
from user_scanner.core.orchestrator import status_validate, Result


def validate_npmjs(user):
    if re.match(r'^[^a-zA-Z0-9_-]', user):
        return Result.error("Username cannot start with a period")

    if re.search(r'[A-Z]', user):
        return Result.error("Username cannot contain uppercase letters.")

    url = f"https://www.npmjs.com/~{user}"
    show_url = "https://npmjs.com"


    return status_validate(url, 404, 200, show_url=show_url, timeout=3.0, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_npmjs(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result}")