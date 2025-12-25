from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_steam(user):
    url = f"https://steamcommunity.com/id/{user}/"

    def process(response):
        if response.status_code == 200:
            if "Error</title>" in response.text:
                return Result.available()
            else:
                return Result.taken()

        return Result.error("Invalid status code")

    return generic_validate(url, process)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_steam(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
