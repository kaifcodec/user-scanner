import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_battlenet(user: str) -> Result:
    """
    Check username availability on Battle.net via Overwatch player search.

    Battle.net uses BattleTags (Username#1234) but this validator checks
    if the username portion exists in the Overwatch player database.

    Note: This checks Overwatch profiles specifically. A username may exist
    on Battle.net but not have an Overwatch profile, or vice versa.

    API behavior:
        - Returns JSON array with player data if username exists
        - Returns empty array [] if username not found
    """
    # BattleTag username rules: 3-12 chars, letters/numbers, one optional #
    # For this validator, we strip any #1234 discriminator if present
    username = user.split('#')[0]

    if not (3 <= len(username) <= 12):
        return Result.error("Length must be 3-12 characters")

    if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', username):
        return Result.error("Must start with letter, only letters and numbers allowed")

    url = f"https://overwatch.blizzard.com/en-us/search/account-by-name/{username}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
    }

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        try:
            data = response.json()
            if isinstance(data, list) and len(data) == 0:
                return Result.available()
            elif isinstance(data, list) and len(data) > 0:
                return Result.taken()
            else:
                return Result.error("Unexpected response format")
        except Exception:
            return Result.error("Failed to parse response")

    return generic_validate(url, process, headers=headers, timeout=15.0, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_battlenet(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
