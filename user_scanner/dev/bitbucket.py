import re
from user_scanner.core.orchestrator import status_validate, Result


def validate_bitbucket(user: str) -> Result:
    if not (1 <= len(user) <= 30):
        return Result.error("Length must be 1-30 characters.")

    if not re.match(r'^[a-z0-9][a-z0-9_-]*$', user):

        if re.search(r'[A-Z]', user):
            return Result.error("Use lowercase letters only.")

        return Result.error("Only use lowercase letters, numbers, hyphens, and underscores.")

    url = f"https://bitbucket.org/{user}/"

    return status_validate(url, 404, [200, 302], follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_bitbucket(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")




