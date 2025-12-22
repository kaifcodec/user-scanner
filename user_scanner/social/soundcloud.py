from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_soundcloud(user):
    url = f"https://soundcloud.com/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()

        if response.status_code == 200:
            text = response.text

            if f'soundcloud://users:{user}' in text:
                return Result.taken()
            if f'"username":"{user}"' in text:
                return Result.taken()
            if 'soundcloud://users:' in text and '"username":"' in text:
                return Result.taken()

            return Result.available()

        return Result.error()

    return generic_validate(url, process, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_soundcloud(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
