from user_scanner.core.orchestrator import status_validate


def validate_bitbucket(user: str):
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
        print("Error occurred!")
