import json
import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_tiktok(user: str) -> Result:
    if not (2 <= len(user) <= 24):
        return Result.error("Length must be 2-24 characters")

    if user.isdigit():
        return Result.error("Usernames cannot contain numbers only")

    if not re.match(r"^[a-zA-Z0-9_.]+$", user):
        return Result.error(
            "Usernames can only contain letters, numbers, underscores and periods"
        )

    if user.startswith(".") or user.endswith("."):
        return Result.error("Username cannot start nor end with a period")

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    show_url = f"https://www.tiktok.com/@{user}"
    # The profile page is a client-rendered shell that is byte-identical for
    # real and missing handles. The embed page server-renders a userInfo blob
    # for public accounts and answers 400 for everything else.
    url = f"https://www.tiktok.com/embed/@{user}"

    def process(response) -> Result:
        # A private account answers 400 exactly like an unregistered handle,
        # and no public endpoint separates the two, so 400 cannot support a
        # verdict either way.
        if response.status_code == 400:
            return Result.error("No public account (a private one looks the same)")

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        info = _extract_user_info(response.text)
        if not info or not info.get("uniqueId"):
            return Result.error("Unrecognised embed payload")

        extra = {}
        if handle := info.get("uniqueId"):
            extra["username"] = handle
        if nickname := info.get("nickname"):
            extra["name"] = nickname
        if user_id := info.get("id"):
            extra["user_id"] = str(user_id)
        if bio := info.get("signature"):
            extra["bio"] = bio.strip()
        if (followers := info.get("followerCount")) is not None:
            extra["followers"] = str(_unwrap_int32(followers))
        if (following := info.get("followingCount")) is not None:
            extra["following"] = str(_unwrap_int32(following))
        if (likes := info.get("heartCount")) is not None:
            extra["likes"] = str(_unwrap_int32(likes))
        if info.get("verified"):
            extra["verified"] = "true"
        if info.get("privateAccount"):
            extra["private"] = "true"

        media = {}
        if avatar := info.get("avatarThumbUrl"):
            media["avatar"] = avatar

        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=show_url, headers=headers)


def _extract_user_info(html: str) -> dict | None:
    """Parse the ``userInfo`` object out of the embed page's state blob."""
    marker = '"userInfo":'
    start = html.find(marker)
    if start == -1:
        return None

    start += len(marker)
    depth = 0
    for index in range(start, len(html)):
        char = html[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[start : index + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _unwrap_int32(value: int) -> int:
    """Counts above 2^31 arrive from the embed API wrapped into a signed
    32-bit integer, so a negative total is the real one minus 2^32."""
    return value + 2**32 if value < 0 else value
