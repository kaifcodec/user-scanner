import json
import re
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from user_scanner.core.orchestrator import generic_validate, make_request
from user_scanner.core.result import Result

BASE_URL = "https://medal.tv"


def validate_medal(user: str) -> Result:
    profile_url = f"{BASE_URL}/u/{quote(user, safe='')}"

    def process(response):
        if response.status_code == 429:
            return Result.error("Rate limited by Medal")
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        try:
            data = response.json()
        except ValueError:
            return Result.error("Medal returned a non-JSON username response")

        if data.get("valid") is not True:
            return Result.error("Medal rejected the username")
        if data.get("exists") is False:
            return Result.available()
        if data.get("exists") is not True:
            return Result.error("Unexpected Medal username response")

        try:
            profile_response = make_request(profile_url, follow_redirects=True)
        except httpx.HTTPError:
            return Result.taken()
        return _profile_result(profile_response, user)

    return generic_validate(
        f"{BASE_URL}/api/users/username",
        process,
        method="POST",
        json={"username": user},
        show_url=profile_url,
    )


def _profile_result(response, user: str) -> Result:
    match = re.search(
        r"<script>var hydrationData=(.*?)</script>", response.text, re.DOTALL
    )
    if not match:
        return Result.taken()

    try:
        profiles = json.loads(match.group(1)).get("profiles", {})
    except (json.JSONDecodeError, AttributeError):
        return Result.taken()

    profile = next(
        (
            item
            for item in profiles.values()
            if isinstance(item, dict)
            and str(item.get("userName", "")).lower() == user.lower()
        ),
        None,
    )
    if profile is None:
        return Result.taken()

    extra = {
        "user_id": profile.get("userId"),
        "display_name": profile.get("displayName"),
        "bio": profile.get("slogan"),
        "followers": profile.get("followers"),
        "following": profile.get("following"),
        "submissions": profile.get("submissions"),
        "upvotes": profile.get("upvotes"),
    }
    if created_at := _iso_timestamp(profile.get("createdAt")):
        extra["created_at"] = created_at

    achievement_names = [
        achievement["name"]
        for achievement in profile.get("achievements") or []
        if isinstance(achievement, dict) and isinstance(achievement.get("name"), str)
    ]
    if achievement_names:
        extra["achievements"] = ", ".join(achievement_names)

    roles = [role for role in profile.get("roles") or [] if isinstance(role, dict)]
    if role_names := [role["name"] for role in roles if role.get("name")]:
        extra["roles"] = ", ".join(role_names)
    if badge_levels := [
        role["badgeLevelName"] for role in roles if role.get("badgeLevelName")
    ]:
        extra["badge_levels"] = ", ".join(badge_levels)

    if (premium_status := profile.get("premiumType")) not in (None, "", "NONE"):
        extra["premium_status"] = premium_status

    active_state = profile.get("activeGameState") or {}
    active_game = next(
        (
            context
            for context in active_state.get("contexts") or []
            if isinstance(context, dict) and context.get("name")
        ),
        None,
    )
    if active_game:
        extra["active_game"] = active_game["name"]
        if started_at := _iso_timestamp(active_game.get("startedAt")):
            extra["active_game_started_at"] = started_at

    for connection in profile.get("connections") or []:
        if (
            isinstance(connection, dict)
            and connection.get("public")
            and connection.get("provider")
        ):
            extra[connection["provider"]] = connection.get("username")
            extra[f"{connection['provider']}_id"] = connection.get("id")

    media = {
        "avatar": profile.get("thumbnail"),
        "banner": profile.get("animatedCoverPhoto") or profile.get("coverPhoto"),
    }
    return Result.taken(extra=extra, media=media)


def _iso_timestamp(value) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()
