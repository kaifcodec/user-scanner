from user_scanner.core.result import Result
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.helpers import get_random_user_agent

def validate_x(user):
    url = "https://api.twitter.com/i/users/username_available.json"
    show_url = "https://x.com"

    params = {
        "username": user,
        "full_name": "John Doe",
        "email": "johndoe07@gmail.com"
    }

    headers = {
        "Authority": "api.twitter.com",
        "User-Agent": get_random_user_agent(),
    }

    def process(response):
        status = response.status_code

        if status in [401, 403, 429]:
            return Result.error()

        elif status == 200:
            data = response.json()
            if data.get('valid') is True:
                return Result.available()
            elif data.get('reason') == 'taken':
                return Result.taken()
            elif (data.get('reason') == "improper_format" or data.get('reason') == "invalid_username"):
                return Result.error(f"X says: {data.get('desc')}")

        return Result.error()

    return generic_validate(url, process, show_url=show_url, params=params, headers=headers)

if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_x(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")