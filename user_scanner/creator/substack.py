import re
from user_scanner.core.orchestrator import status_validate, Result


def validate_substack(user: str) -> Result:
    if not (4 <= len(user) <= 32):
        return Result.error("Length must be 4-32 characters")

    if not re.match(r'^[a-z0-9]+$', user):
        if re.search(r'[A-Z]', user):
            return Result.error("Use lowercase letters only")
        return Result.error("Usernames can only contain lowercase letters and numbers")

    url = f"https://{user}.substack.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Encoding': "identity",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=0, i"
    }

    return status_validate(url, 404, 200, headers=headers, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_substack(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
