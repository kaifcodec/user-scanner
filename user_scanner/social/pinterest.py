from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

def validate_pinterest(user):
    url = f"https://www.pinterest.com/{user}/"

    def process(response):
        if response.status_code == 200:
            if "User not found." in response.text:
                return Result.available()
            else:
                return Result.taken()
        else:
            return Result.error("Invalid status code")

    return generic_validate(url, process, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_pinterest(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
