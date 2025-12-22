from user_scanner.core.result import Result
from user_scanner.core.orchestrator import generic_validate

def validate_discord(user):
    url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"

    headers = {
        "authority": "discord.com",
        "accept": "/",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "content-type": "application/json",
        "origin": "https://discord.com",
        "referer": "https://discord.com/register"
    }

    data = {"username": user}

    def process(response):
        if response.status_code == 200:
            status = response.json().get("taken")
            if status is True:
                return Result.taken()
            elif status is False:
                return Result.available()
        return Result.error("Invalid status code")

    return generic_validate(url, process, method="POST", json=data, headers=headers, timeout=3.0)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_discord(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
