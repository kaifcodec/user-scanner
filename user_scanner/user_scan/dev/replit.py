from user_scanner.core.orchestrator import status_validate


def validate_replit(user):
    url = f"https://replit.com/@{user}"
    show_url = "https://replit.com"

    return status_validate(url, 404, 200, show_url=show_url, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_replit(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")