from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_bluesky(user):
    handle = user if user.endswith(".bsky.social") else f"{user}.bsky.social"
    url = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile"

    def process(response):
        if response.status_code == 200:
            data = response.json()
            extra = {}
            if data.get("displayName"):
                extra["display_name"] = data["displayName"]
            if data.get("description"):
                extra["bio"] = data["description"].strip()
            if data.get("followersCount") is not None:
                extra["followers"] = data["followersCount"]
            if data.get("followsCount") is not None:
                extra["following"] = data["followsCount"]
            if data.get("postsCount") is not None:
                extra["posts"] = data["postsCount"]
            if data.get("avatar"):
                media = {"avatar": data["avatar"]}
            else:
                media = {}
            return Result.taken(extra=extra, media=media)

        if response.status_code == 400:
            message = response.json().get("message")
            if message == "Profile not found":
                return Result.available()
            return Result.error(message or "Invalid Bluesky handle")

        return Result.error(f"HTTP {response.status_code}, report it via GitHub issues")

    return generic_validate(
        url,
        process,
        show_url=f"https://bsky.app/profile/{handle}",
        headers={"User-Agent": get_random_user_agent()},
        params={"actor": handle},
        timeout=15.0,
    )
