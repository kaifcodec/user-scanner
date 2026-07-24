import re
import json

from user_scanner.core.impersonate import impersonate_request
from user_scanner.core.result import Result

BASE_URL = "https://www.camsoda.com"
# The signup form's live availability check. It answers for every account,
# broadcaster or plain member (members have no public /<user> page), so it is the
# authoritative existence signal; the profile page is fetched only to enrich.
CHECK_URL = f"{BASE_URL}/api/v1/user/check"
CHECK_HEADERS = {"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE_URL}/register"}
# Handles shorter than this are reserved/invalid and the check reports them as
# taken even when no account owns them, so they are not a reliable verdict.
MIN_USERNAME_LENGTH = 3

# Profile fields worth surfacing, mapped to friendlier extra keys.
FIELDS = {
    "displayName": "name",
    "id": "user_id",
    "gender": "gender",
    "createdAt": "created_at",
    "status": "status",
    "avatarUrl": "avatar",
    "profilePictureUrl": "profile_picture",
}


def validate_camsoda(user: str) -> Result:
    show_url = f"{BASE_URL}/{user}"

    if len(user.strip()) < MIN_USERNAME_LENGTH:
        return Result.error(
            f"Username too short (min {MIN_USERNAME_LENGTH} characters)", url=show_url)

    try:
        match = _name_taken(user)
    except Exception as e:
        return Result.error(e, url=show_url)

    if match is None:
        return Result.error("Name check gave no verdict", url=show_url)
    if not match:
        return Result.available(url=show_url)

    # Taken. Broadcasters expose a rich public profile; plain members do not, so
    # a failed enrichment just means the account is a member.
    return Result.taken(extra=_broadcaster_profile(user), url=show_url)


def _name_taken(user: str) -> bool | None:
    """Query the availability check. Returns True when an account owns the
    handle, False when it is free, None when the response is unreadable. The
    endpoint is case-insensitive and trims whitespace, matching the site."""
    response = impersonate_request(
        CHECK_URL, params={"type": "username", "value": user},
        headers=CHECK_HEADERS, allow_redirects=True)
    if response.status_code != 200:
        return None
    try:
        return json.loads(response.text).get("match") == 1
    except json.JSONDecodeError:
        return None


def _broadcaster_profile(user: str) -> dict:
    """Best-effort enrichment: broadcasters answer /<user> with an embedded
    profile object; members 404 here, so a miss yields only the account type."""
    try:
        response = impersonate_request(f"{BASE_URL}/{user}", allow_redirects=True)
        if response.status_code != 200:
            return {"type": "member"}
        profile = _user_object(response.text, user)
        if not profile:
            return {"type": "member"}
        return {"type": "broadcaster", **_extract_profile(profile)}
    except Exception:
        return {"type": "member"}


def _user_object(html_text: str, user: str) -> dict:
    """Pull the preloaded-state `user` object whose username matches the
    request. Recommendation carousels embed sibling `"user":{...}` nodes, so
    each candidate is parsed and matched rather than taking the first."""
    for match in re.finditer(r'"user":\{', html_text):
        raw = _json_object_at(html_text, match.end() - 1)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if str(data.get("username", "")).lower() == user.lower():
            return data
    return {}


def _json_object_at(text: str, start: int) -> str | None:
    # Brace-match from an opening '{', ignoring braces inside string literals,
    # to slice out a complete JSON object embedded in the page.
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        char = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _extract_profile(profile: dict) -> dict:
    extra = {}

    for key, label in FIELDS.items():
        value = profile.get(key)
        if value in (None, "", [], {}):
            continue
        extra[label] = re.sub(r"\s+", " ", str(value)).strip()

    follower = profile.get("follower") or {}
    if follower.get("countTotal"):
        extra["followers"] = str(follower["countTotal"])

    # The user rating is a 0-100 score; the sibling entries are payout stats.
    ratings = profile.get("ratings") or {}
    if ratings.get("user"):
        extra["rating"] = str(ratings["user"])

    tags = [x for x in (profile.get("tagList") or []) if isinstance(x, str)]
    if tags:
        extra["tags"] = ", ".join(tags)

    return extra
