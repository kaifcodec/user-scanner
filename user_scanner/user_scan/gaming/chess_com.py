import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_chess_com(user: str) -> Result:
    if not (3 <= len(user) <= 25):
        return Result.available("Username must be between 3 and 25 characters")

    if not re.match(r"^[a-zA-Z0-9_-]+$", user):
        return Result.available(
            "Usernames can only contain letters, numbers, underscores, and hyphens"
        )

    if not (user[0].isalnum() and user[-1].isalnum()):
        return Result.available("Username must start and end with a letter or number")

    url = f"https://api.chess.com/pub/player/{user}"
    show_url = f"https://www.chess.com/member/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                extra = {}
                if name := data.get("name"): extra["name"] = name
                if username := data.get("username"): extra["username"] = username
                if title := data.get("title"): extra["title"] = title
                if status := data.get("status"): extra["status"] = status
                if league := data.get("league"): extra["league"] = league
                if location := data.get("location"): extra["location"] = location
                if followers := data.get("followers"): extra["followers"] = str(followers)
                if avatar := data.get("avatar"): extra["avatar"] = avatar
                if twitch := data.get("twitch_url"): extra["links"] = twitch
                return Result.taken(extra=extra)
            except Exception:
                pass
            return Result.error("200 response status with no recognizable data, report it via GitHub issues")
        elif response.status_code == 404:
            return Result.available()
        
        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
