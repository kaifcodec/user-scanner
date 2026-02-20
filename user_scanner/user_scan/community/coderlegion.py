from user_scanner.core.orchestrator import status_validate


def validate_coderlegion(user):
    url = f"https://coderlegion.com/user/{user}"
    show_url = "https://coderlegion.com"

    return status_validate(url, 404, 200, show_url=show_url, timeout=15.0)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_coderlegion(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")