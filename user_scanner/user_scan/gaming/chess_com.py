import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


def validate_chess_com(user: str) -> Result:
    # Length must be between 3 and 25 characters
    if not (3 <= len(user) <= 25):
        return Result.error("Length must be 3-25 characters")

    # Only letters, numbers, underscores, and dashes allowed
    if not re.match(r'^[a-zA-Z0-9_-]+$', user):
        return Result.error("Usernames can only contain letters, numbers, underscores, and hyphens")

    # Must start and end with an alphanumeric character
    if not (user[0].isalnum() and user[-1].isalnum()):
        return Result.error("Username must start and end with a letter or number")

    url = f"https://www.chess.com/callback/user/valid?username={user}"
    show_url = "https://chess.com"

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Accept-Language': "en-US,en;q=0.9",
    }

    def process(response):
        if response.status_code == 200:
            data = response.json()
            if data.get('valid') is True:
                # 'valid': true means the username is NOT taken
                return Result.available()
            elif data.get('valid') is False:
                # 'valid': false means the username IS taken
                return Result.taken()
        return Result.error("Invalid status code")

    return generic_validate(url, process, show_url=show_url, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_chess_com(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
