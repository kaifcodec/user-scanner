from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_chess_com(user):
    url = f"https://www.chess.com/callback/user/valid?username={user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
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

    return generic_validate(url, process, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_chess_com(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
