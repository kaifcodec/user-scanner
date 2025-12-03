from user_scanner.core.orchestrator import status_validate


def validate_dockerhub(user):
    url = f"https://hub.docker.com/v2/users/{user}/"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        'Accept': "application/json",
    }

    return status_validate(url, 404, 200, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_dockerhub(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
