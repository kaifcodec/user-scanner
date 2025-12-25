from user_scanner.core.orchestrator import status_validate


def validate_patreon(user):
    url = f"https://www.patreon.com/{user}"

    return status_validate(url, 404, 200, timeout=15.0, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_patreon(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
