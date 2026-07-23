import json
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://e621.net"

# e621's API terms require a descriptive, identifying User-Agent; generic or
# spoofed browser agents get throttled or blocked.
HEADERS = {
    "User-Agent": "user-scanner (OSINT username checker; +https://github.com/kaifcodec/user-scanner)",
    "Accept": "application/json",
}

# Scalar profile fields, mapped to friendlier extra keys.
FIELDS = {
    "id": "user_id",
    "level_string": "level",
    "created_at": "joined",
    "is_banned": "is_banned",
    "is_verified": "is_verified",
}

# Activity counters, surfaced only when non-zero.
COUNTERS = {
    "post_upload_count": "uploads",
    "post_update_count": "post_edits",
    "note_update_count": "note_edits",
    "comment_count": "comments",
    "favorite_count": "favorites",
    "forum_post_count": "forum_posts",
    "wiki_page_version_count": "wiki_edits",
    "artist_version_count": "artist_edits",
    "pool_version_count": "pool_edits",
    "flag_count": "flags",
    "positive_feedback_count": "positive_feedback",
    "neutral_feedback_count": "neutral_feedback",
    "negative_feedback_count": "negative_feedback",
}


def validate_e621(user: str) -> Result:
    url = f"{BASE_URL}/users/{user}.json"
    show_url = f"{BASE_URL}/users/{user}"

    def process(response):
        # The API reports a missing account as 404 with an explicit reason.
        if response.status_code == 404:
            if _reason(response.text) == "not found":
                return Result.available(url=show_url)
            return Result.error("Unexpected 404 (not the not-found payload)", url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        try:
            profile = json.loads(response.text)
        except json.JSONDecodeError:
            return Result.error("Profile response was not JSON", url=show_url)

        # Confirm the payload describes the handle we asked for; the endpoint
        # also resolves numeric ids, which would otherwise pass silently.
        if str(profile.get("name", "")).lower() != user.lower():
            return Result.error("Profile confirmation not found", url=show_url)

        return Result.taken(extra=_extract_profile(profile), url=show_url)

    return impersonate_validate(url, process, show_url=show_url, headers=HEADERS)


def _reason(body: str) -> str:
    try:
        return str(json.loads(body).get("reason", "")).strip().lower()
    except (json.JSONDecodeError, AttributeError):
        return ""


def _extract_profile(profile: dict) -> dict:
    extra = {}

    for key, label in FIELDS.items():
        value = profile.get(key)
        if value is None or value == "":
            continue
        extra[label] = str(value).split("T")[0] if key == "created_at" else str(value)

    for key, label in COUNTERS.items():
        value = profile.get(key)
        if isinstance(value, int) and value:
            extra[label] = str(value)

    # The avatar is a regular post, so link it rather than reporting a bare id.
    avatar_id = profile.get("avatar_id")
    if avatar_id:
        extra["avatar"] = f"{BASE_URL}/posts/{avatar_id}"

    for key, label in (("profile_about", "about"), ("profile_artinfo", "artist_info")):
        text = re.sub(r"\s+", " ", str(profile.get(key) or "")).strip()
        if text:
            extra[label] = text

    return extra
