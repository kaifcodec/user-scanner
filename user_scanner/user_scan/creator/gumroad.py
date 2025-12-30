import re
from user_scanner.core.orchestrator import status_validate, Result

def validate_gumroad(user: str) -> Result:
    if not re.fullmatch(r"[a-z0-9]{3,20}", user):
        return Result.error("Username must be between 3 and 20 lowercase alphanumeric characters")

    url = f"https://{user}.gumroad.com/"
    return status_validate(url, 404, 200, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_gumroad(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")

