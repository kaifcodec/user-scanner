from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

def validate_stackoverflow(user: str) -> Result:
    url = f"https://stackoverflow.com/users/filter?search={user}"

    def process(response):
        if response.status_code == 200:
            text = response.text

            if "No users matched your search." in text:
                return Result.available()

            pattern = f'>{user}<'
            if pattern in text:
                return Result.taken()

            return Result.available()

        return Result.error("Unexpected status code from Stack Overflow")

    return generic_validate(url, process)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_stackoverflow(user)

    if result == Result.available():
        print("Available!")
    elif result == Result.taken():
        print("Unavailable!")
    else:
        msg = result.get_reason()
        print("Error occurred!" + msg)
