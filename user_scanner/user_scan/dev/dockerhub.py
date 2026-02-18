from user_scanner.core.orchestrator import status_validate
from user_scanner.core.helpers import get_random_user_agent


def validate_dockerhub(user):
    url = f"https://hub.docker.com/v2/users/{user}/"

    headers = {
        'User-Agent': get_random_user_agent(),
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
