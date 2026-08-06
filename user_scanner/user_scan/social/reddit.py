import html
import json
import re
from datetime import datetime, timezone

from user_scanner.core.impersonate import impersonate_request
from user_scanner.core.result import Result

BASE_URL = "https://www.reddit.com"
# The signup form's live availability check. It is the only surface that answers
# for suspended and deleted accounts, which the public profile page renders with
# the same "Sorry, nobody on Reddit goes by that name" page as a free handle.
AVAILABLE_URL = f"{BASE_URL}/api/username_available.json"

# Reddit answers an uncleared session with a bot wall and every JSON endpoint
# with a hard 403; clearance is only offered on an HTML page. The first hit
# returns a reCAPTCHA interstitial that sets the cookie, the second a
# proof-of-work whose solution is its seed repeated twice.
CHALLENGE_TITLE = "Prove your humanity"
CHALLENGE_SEED_RE = re.compile(r'\(async e=>e\+e\)\("([0-9a-f]+)"\)')
CHALLENGE_TOKEN_RE = re.compile(r'name="token" value="([0-9a-f]+)"')
CHALLENGE_ATTEMPTS = 3

BOOLEAN_FLAGS = {
    "is_employee": "employee",
    "is_mod": "moderator",
    "is_gold": "premium",
    "has_verified_email": "verified_email",
}
KARMA_FIELDS = {
    "total_karma": "karma_total",
    "link_karma": "karma_post",
    "comment_karma": "karma_comment",
    "awardee_karma": "karma_awardee",
    "awarder_karma": "karma_awarder",
}


def validate_reddit(user: str) -> Result:
    show_url = f"{BASE_URL}/user/{user}/"

    try:
        _clear_bot_wall()
        available = _name_available(user)
    except Exception as e:
        return Result.error(e, url=show_url)

    if available is None:
        return Result.error(
            "Availability check gave no verdict (invalid name or blocked)", url=show_url)
    if available:
        return Result.available(url=show_url)

    extra, media = _profile(user)
    return Result.taken(extra=extra, media=media, url=show_url)


def _clear_bot_wall() -> None:
    """Walk the interstitial chain until the shared session holds a clearance
    cookie. A session that is already cleared answers with the real homepage on
    the first hit, so this costs one request per scan after the first module."""
    for _ in range(CHALLENGE_ATTEMPTS):
        response = impersonate_request(f"{BASE_URL}/", allow_redirects=True)
        params = _challenge_params(response.text)
        if params:
            impersonate_request(f"{BASE_URL}/", params=params, allow_redirects=True)
            return
        if CHALLENGE_TITLE not in response.text:
            return


def _challenge_params(page: str) -> dict[str, str] | None:
    seed = CHALLENGE_SEED_RE.search(page)
    token = CHALLENGE_TOKEN_RE.search(page)
    if not seed or not token:
        return None
    return {
        "solution": seed.group(1) * 2,
        "js_challenge": "1",
        "token": token.group(1),
        "jsc_orig_r": "",
    }


def _name_available(user: str) -> bool | None:
    """Ask the signup check whether the handle is free. Returns None when the
    endpoint rejects the name as malformed (`BAD_USERNAME`) or answers
    unreadably — neither is a verdict about an account existing."""
    response = impersonate_request(
        AVAILABLE_URL, params={"user": user}, allow_redirects=True)
    if response.status_code != 200:
        return None
    try:
        verdict = json.loads(response.text)
    except json.JSONDecodeError:
        return None
    return verdict if isinstance(verdict, bool) else None


def _profile(user: str) -> tuple[dict, dict]:
    """Best-effort enrichment. Deleted accounts keep their handle reserved but
    404 here, and suspended ones expose only their name, so a thin answer is
    reported as the account status rather than as missing data."""
    try:
        response = impersonate_request(
            f"{BASE_URL}/user/{user}/about.json", allow_redirects=True)
    except Exception:
        return {}, {}

    if response.status_code == 404:
        return {"status": "deleted"}, {}
    if response.status_code != 200:
        return {}, {}

    try:
        data = json.loads(response.text).get("data") or {}
    except json.JSONDecodeError:
        return {}, {}
    if not data.get("name"):
        return {}, {}
    if data.get("is_suspended"):
        # A suspended account reports every karma figure as 0; only its name is real.
        return {"name": data["name"], "status": "suspended"}, {}

    return _extract_profile(data), _extract_media(data)


def _extract_profile(data: dict) -> dict:
    profile = data.get("subreddit") or {}
    extra: dict[str, str | bool | int] = {"name": data["name"], "status": "active"}

    if data.get("id"):
        extra["id"] = f"t2_{data['id']}"

    title = profile.get("title")
    if title and title != data["name"]:
        extra["display_name"] = title

    description = profile.get("public_description")
    if description:
        extra["bio"] = re.sub(r"\s+", " ", description).strip()

    created = _created_at(data.get("created_utc"))
    if created:
        extra["created"] = created

    for field, label in KARMA_FIELDS.items():
        value = data.get(field)
        if isinstance(value, int):
            extra[label] = value

    for field, label in BOOLEAN_FLAGS.items():
        if data.get(field):
            extra[label] = True

    if profile.get("over_18"):
        extra["nsfw"] = True

    return extra


def _created_at(created_utc: object) -> str | None:
    if not isinstance(created_utc, (int, float)):
        return None
    return datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d")


def _extract_media(data: dict) -> dict:
    profile = data.get("subreddit") or {}
    media = {
        "avatar": data.get("icon_img") or profile.get("icon_img"),
        "snoovatar": data.get("snoovatar_img"),
        "banner": profile.get("banner_img"),
    }
    # about.json serves these URLs HTML-escaped, so their query strings arrive
    # with `&amp;` separators and 404 unless unescaped.
    return {key: html.unescape(value) for key, value in media.items() if value}
