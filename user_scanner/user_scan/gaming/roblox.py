from urllib.parse import urlencode

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import (
    generic_validate,
    make_request,
    status_validate,
)
from user_scanner.core.result import Result


def _get_avatar_picture(user_id: int) -> str | None:
    # https://create.roblox.com/docs/cloud/reference/domains/thumbnails#thumbnails_get_v1_users_avatar_headshot

    query = urlencode(
        {
            "userIds": user_id,
            "includeBackground": "false",
            "size": "720x720",
            "format": "Png",
            "isCircular": "false",
        }
    )

    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?{query}"
    response = make_request(url, headers={"accept": "*/*"})

    if response.status_code != 200:
        return None

    data = response.json().get("data", [])
    entry = next(iter(data), None)
    if not entry or entry.get("state") != "Completed":
        return None

    return entry.get("imageUrl")


def _fetch_user_details(uid: int) -> dict:
    extra: dict = {}

    try:
        response = make_request(
            f"https://users.roblox.com/v1/users/{uid}", follow_redirects=True
        )
        if response.status_code != 200:
            return extra

        data = response.json()
        if desc := data.get("description"):
            extra["bio"] = desc
        if created := data.get("created"):
            extra["created"] = created
        if data.get("isBanned"):
            extra["banned"] = "Yes"

    except Exception:
        pass

    return extra


def process(response):
    if response.status_code == 429:
        return Result.error("Too many requests")
    if response.status_code == 400:
        return Result.error("Invalid username")
    if response.status_code != 200:
        return Result.available()

    try:
        data = response.json().get("data", [])
        if not data:
            return Result.available()

        entry = data[0]
        uid = entry.get("id")
        extra = {
            "display name": entry.get("displayName"),
            "uid": uid,
            "is verified": entry.get("hasVerifiedBadge"),
        }
        media = {}

        if uid:
            extra.update(_fetch_user_details(uid))
            if get_avatar_url := _get_avatar_picture(uid):
                media["avatar"] = get_avatar_url

        return Result.taken(
            extra=extra,
            media=media,
            url=f"https://www.roblox.com/users/{uid}" if uid else None,
        )

    except Exception:
        pass

    return Result.available()


def validate_roblox(user: str) -> Result:
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    result = generic_validate(
        "https://users.roblox.com/v1/usernames/users",
        process,
        method="POST",
        json={"usernames": [user], "excludeBannedUsers": False},
        headers=headers,
        follow_redirects=True,
    )

    if result.get_reason() != "Too many requests":
        return result

    # If rate limited, uses a simple status validation
    return status_validate(
        "https://www.roblox.com/user.aspx",
        404,
        [200, 302],
        show_url="https://roblox.com",
        follow_redirects=True,
        params={"username": user},
    )
