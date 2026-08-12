import html
import re
from datetime import datetime, timezone

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://www.7cups.com"

# Public profile pages sit behind an AWS WAF JS challenge no HTTP client can
# clear; this JSON endpoint backs the same page and is served unchallenged.
API_URL = f"{BASE_URL}/apiv2/user"

USER_TYPES = {"l": "listener", "m": "member", "t": "therapist"}


def validate_7cups(user: str) -> Result:
    show_url = f"{BASE_URL}/@{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()

        if response.status_code == 202 or "x-amzn-waf-action" in response.headers:
            return Result.error("AWS WAF challenge triggered")

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        try:
            data = response.json()
        except Exception:
            return Result.error("Profile response was not JSON")

        if not isinstance(data, dict) or not data.get("screenName"):
            return Result.error("200 response with no profile data")

        extra, media = _extract(data)
        return Result.taken(extra=extra, media=media)

    return impersonate_validate(f"{API_URL}/{user}", process, show_url=show_url)


def _extract(data: dict) -> tuple[dict, dict]:
    extra: dict = {"screen_name": data["screenName"]}
    media: dict = {}

    # `listType` names the listener sub-role; plain accounts only carry userType.
    account_type = data.get("listType") or USER_TYPES.get(str(data.get("userType", "")))
    if account_type:
        extra["type"] = account_type

    if user_id := (data.get("userID") or data.get("memID") or data.get("listID")):
        extra["user_id"] = user_id
    if bio := _plain_text(data.get("bio")):
        extra["bio"] = bio
    if quote := _plain_text(data.get("quote")):
        extra["quote"] = quote
    if age := data.get("age"):
        extra["age"] = str(age)
    if country := data.get("Country"):
        extra["country"] = country
    if language := data.get("language"):
        extra["language"] = language
    if joined := _date(data.get("signupDateU")):
        extra["joined"] = joined
    if approved := _date(data.get("approvalDateU")):
        extra["listener_since"] = approved
    if level := (data.get("listenerLevel") or data.get("memberLevel")):
        extra["level"] = level
    if points := data.get("points_formatted"):
        extra["points"] = points
    if data.get("numConversations"):
        extra["conversations"] = str(data["numConversations"])
    if data.get("compassionHearts"):
        extra["compassion_hearts"] = str(data["compassionHearts"])
    if data.get("forumUpvotes"):
        extra["forum_upvotes"] = str(data["forumUpvotes"])
    if rating := data.get("overallRating"):
        extra["rating"] = f"{rating} ({data.get('R_numratings', 0)} ratings)"
    if last_active := data.get("lastActive"):
        extra["last_active"] = last_active
    if data.get("onlineNow"):
        extra["online"] = "Yes"
    if badges := [b.get("badgeName") for b in data.get("badges", []) if b.get("active")]:
        extra["badges"] = ", ".join(filter(None, badges))

    avatar = data.get("imgURL") or data.get("image")
    if avatar:
        media["avatar"] = avatar if avatar.startswith("http") else f"{BASE_URL}{avatar}"

    return extra, media


def _plain_text(value) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def _date(timestamp) -> str:
    try:
        return datetime.fromtimestamp(int(timestamp), tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return ""
