import re

from user_scanner.core.orchestrator import Result, generic_validate
from user_scanner.core.helpers import get_random_user_agent


def validate_lichess(user: str) -> Result:
    if not (2 <= len(user) <= 20):
        return Result.available("Username must be between 2 and 20 characters")

    if not re.match(r"^[a-zA-Z0-9_-]+$", user):
        return Result.available(
            "Usernames can only contain letters, numbers, underscores, and hyphens"
        )

    if re.search(r"[_-]{2,}", user):
        return Result.available(
            "Username cannot contain consecutive underscores or hyphens"
        )

    if not re.match(r".*[a-zA-Z0-9]$", user):
        return Result.available("Username must end with a letter or a number")

    url = f"https://lichess.org/api/user/{user}"
    show_url = f"https://lichess.org/@/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                extra = {}
                profile = data.get("profile", {})
                if real_name := profile.get("realName"): extra["name"] = real_name
                if bio := profile.get("bio"): extra["bio"] = bio
                
                links = []
                if profile_links := profile.get("links"):
                    links.append(profile_links)
                if streamer_info := data.get("streamer"):
                    if twitch := streamer_info.get("twitch"):
                        if ch := twitch.get("channel"): links.append(ch)
                    if youtube := streamer_info.get("youtube"):
                        if ch := youtube.get("channel"): links.append(ch)
                if links:
                    extra["links"] = ", ".join(list(dict.fromkeys(links)))

                if data.get("patron"): extra["patron"] = "Yes"
                if data.get("verified"): extra["verified"] = "Yes"
                return Result.taken(extra=extra)
            except Exception:
                pass
            return Result.taken()
        elif response.status_code == 404:
            return Result.available()
        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
