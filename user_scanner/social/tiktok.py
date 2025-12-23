import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_tiktok(user: str) -> Result:
    if not (2 <= len(user) <= 24):
        return Result.error("Length must be 2-24 characters")

    if user.isdigit():
        return Result.error("Usernames cannot contain numbers only")

    if not re.match(r'^[a-zA-Z0-9_.]+$', user):
        return Result.error("Usernames can only contain letters, numbers, underscores and periods")

    if user.startswith(".") or user.endswith("."):
        return Result.error("Username cannot start nor end with a period")

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        'Accept-Encoding': "identity",
        'Accept-Language': "en-US,en;q=0.9",
        'sec-fetch-dest': "document",
        'Connection': "keep-alive"
    }

    url = f"https://www.tiktok.com/@{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            if "statuscode\":10221" in response.text.lower():
                return Result.available()
            else:
                return Result.taken()
        return Result.error("Unable to load tiktok")

    return generic_validate(url, process, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_tiktok(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
