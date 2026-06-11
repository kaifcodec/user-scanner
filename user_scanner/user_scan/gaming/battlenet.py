import re

from user_scanner.core.helpers import get_random_user_agent
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
    username = user.split("#")[0]

    if not (3 <= len(username) <= 12):
        return Result.available("Username must be between 3 and 12 characters")

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9]*$", username):
        return Result.available("Username must start with a letter and contain only letters and numbers")

    url = f"https://overwatch.blizzard.com/en-us/search/account-by-name/{username}"
    show_url = f"https://overwatch.blizzard.com/en-us/search/account-by-name/{username}/"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
    }

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        try:
            data = response.json()

            if isinstance(data, list) and len(data) == 0:
                return Result.available(
                    "Battle.net allows duplicate usernames and distinguishes accounts with a numeric tag"
                )
            elif isinstance(data, list) and len(data) > 0:
                extra = {}
                match_list = []
                for item in data[:5]:
                    name = item.get("name")
                    is_public = "Public" if item.get("isPublic") else "Private"
                    title = item.get("title", {})
                    title_en = title.get("en_US") if isinstance(title, dict) else ""
                    title_str = f" ({title_en})" if title_en else ""
                    match_list.append(f"{name}{title_str} [{is_public}]")
                if match_list:
                    extra["matches"] = ", ".join(match_list)
                return Result.taken(extra=extra)
            else:
                return Result.error("Unexpected response format")
        except Exception:
            return Result.error("Failed to parse response")

    return generic_validate(
        url,
        process,
        show_url=show_url,
        headers=headers,
        timeout=6.0,
        follow_redirects=True,
    )
