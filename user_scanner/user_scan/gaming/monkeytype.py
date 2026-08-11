from datetime import datetime, timezone
from urllib.parse import quote

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

API = "https://api.monkeytype.com"


def validate_monkeytype(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"{API}/users/checkName/{safe_user}"
    show_url = f"https://monkeytype.com/profile/{safe_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "identity",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        data = {}
        try:
            data = response.json()
        except Exception:
            pass

        if response.status_code == 200:
            # Expected shape:
            # { "message": "string", "data": { "available": true/false } }
            available = data.get("data", {}).get("available")

            if available is True:
                return Result.available()
            elif available is False:
                profile = _fetch_profile(safe_user, show_url, headers)
                return profile if profile.is_found() else Result.taken()

        # Surface Monkeytype validation errors (e.g. special characters)
        errors = data.get("validationErrors")
        if errors:
            # The name filter also rejects names that predate it, so a rejected
            # name can still belong to an account the profile endpoint serves.
            profile = _fetch_profile(safe_user, show_url, headers)
            return profile if profile.is_found() else Result.error("; ".join(errors))

        return Result.error("Invalid status code")

    return generic_validate(url, process, show_url=show_url, headers=headers)


def _fetch_profile(safe_user: str, show_url: str, headers: dict) -> Result:
    """Public profile metadata as a taken Result, or an error Result when the
    name serves no profile. Resolves names case-insensitively."""
    url = f"{API}/users/{safe_user}/profile?isUid=false"

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        data = response.json().get("data", {})
        name = data.get("name")
        if not name:
            return Result.error("Profile response carried no account")

        media = {}
        # Monkeytype renders the linked Discord avatar as the profile picture.
        discord_id, avatar = data.get("discordId"), data.get("discordAvatar")
        if discord_id and avatar:
            media["avatar"] = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png"

        return Result.taken(extra=_profile_extra(data, name), media=media)

    return generic_validate(url, process, show_url=show_url, headers=headers)


def _profile_extra(data: dict, name: str) -> dict:
    extra = {"username": name}

    if data.get("banned"): extra["banned"] = "Yes"
    if data.get("isPremium"): extra["premium"] = "Yes"
    if uid := data.get("uid"): extra["uid"] = uid
    if added_at := data.get("addedAt"): extra["joined"] = _to_date(added_at)

    details = data.get("details") or {}
    if bio := details.get("bio"): extra["bio"] = bio
    if keyboard := details.get("keyboard"): extra["keyboard"] = keyboard

    socials = details.get("socialProfiles") or {}
    for field in ("github", "twitter", "website"):
        if handle := socials.get(field): extra[field] = handle

    # Discord's numeric snowflake, which no public lookup resolves to a handle.
    if discord_id := data.get("discordId"): extra["discord_id"] = discord_id

    stats = data.get("typingStats") or {}
    if completed := stats.get("completedTests"): extra["tests_completed"] = str(completed)
    if seconds := stats.get("timeTyping"): extra["time_typing"] = _to_duration(seconds)
    if best_wpm := _best_wpm(data.get("personalBests")): extra["best_wpm"] = f"{best_wpm:g}"
    if xp := data.get("xp"): extra["xp"] = str(int(xp))
    if streak := data.get("maxStreak"): extra["max_streak"] = f"{streak} days"

    return extra


def _to_date(epoch_ms: int) -> str:
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def _to_duration(seconds: float) -> str:
    if seconds < 3600:
        return f"{seconds / 60:.0f} minutes"
    return f"{seconds / 3600:.1f} hours"


def _best_wpm(personal_bests) -> float:
    if not isinstance(personal_bests, dict):
        return 0.0

    scores = [
        entry.get("wpm") or 0
        for mode in personal_bests.values()
        if isinstance(mode, dict)
        for entries in mode.values()
        for entry in entries
        if isinstance(entry, dict)
    ]
    return max(scores, default=0.0)
