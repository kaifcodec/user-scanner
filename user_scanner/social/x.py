import httpx
import json
from colorama import Fore, Style
from httpx import ConnectError, TimeoutException

from user_scanner.core.orchestrator import Result


def validate_x(user):
    url = "https://api.twitter.com/i/users/username_available.json"

    params = {
        "username": user,
        "full_name": "John Doe",
        "email": "johndoe07@gmail.com"
    }

    headers = {
        "Authority": "api.twitter.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    }

    try:
        response = httpx.get(url, params=params, headers=headers, timeout=3.0)
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
                return Result.error(f"{Fore.CYAN}{Fore.CYAN}X says: {data.get('desc')}{Style.RESET_ALL}")

        return Result.error()

    except (ConnectError, TimeoutException, json.JSONDecodeError):
        return 2
    except Exception:
        return 2


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_x(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
