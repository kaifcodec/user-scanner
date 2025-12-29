from user_scanner.core.orchestrator import status_validate, Result

def validate_gumroad(user: str) -> Result:
    if not 3 <= len(user) <= 20:
        return Result.error("Username must be between 3 and 20 characters.")

    if user != user.lower():
        return Result.error("Use lowercase letters only.")

    if not user.isascii() or not user.isalnum():
        return Result.error("Only use lowercase letters and numbers only.")

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
