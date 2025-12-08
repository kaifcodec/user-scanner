from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_reddit(user):
    url = f"https://www.reddit.com/user/{user}/"

    def process(response):
        if response.status_code == 200:
            if "Sorry, nobody on Reddit goes by that name." in response.text:
                return Result.available()
            else:
                return Result.taken()
        else:
            return Result.error()

    return generic_validate(url, process, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_reddit(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
