import json
import re
from datetime import datetime, timezone
from typing import Callable, Optional

from user_scanner.core.impersonate import impersonate_request
from user_scanner.core.result import Result

# Medium's JSON views prefix their payload with this anti-hijacking guard.
JSON_GUARD = "])}while(1);</x>"

# The HTML profile answers unknown handles with 200 and renders its 404 view, so
# the status code carries no verdict there — only these body markers do.
NOT_FOUND_MARKERS = (">PAGE NOT FOUND<", "Out of nothing, something.")

AVATAR_CDN = "https://miro.medium.com/v2/resize:fit:2400/"


def validate_medium(user: str) -> Result:
    """Medium serves an existing account through Cloudflare, which answers 403
    in some regions while unknown handles still render their 404 view — so one
    view alone can confirm a miss and never a hit. Each view is tried until one
    carries a verdict.
    """
    show_url = f"https://medium.com/@{user}"
    views: tuple[tuple[str, Callable[[str], Optional[Result]]], ...] = (
        ("profile JSON", _from_json_view),
        ("HTML profile", _from_profile_page),
        ("story feed", _from_feed),
    )

    failures = []
    for label, view in views:
        try:
            result = view(user)
        except Exception as e:
            err_msg = str(e).strip() or type(e).__name__
            failures.append(f"{label}: {err_msg}")
            continue
        if result:
            return result.update(url=show_url)

    if failures:
        first_err = failures[0].strip()
        reason = (
            first_err
            if first_err and not first_err.endswith(":")
            else "Profile view request failed"
        )
        return Result.error(reason, url=show_url)

    return Result.error("Every profile view was blocked before a verdict", url=show_url)


def _from_json_view(user: str) -> Optional[Result]:
    """Medium's own profile JSON: authoritative on existence, and the only view
    that tells a suspended account apart from a free handle.
    """
    response = impersonate_request(
        f"https://medium.com/@{user}?format=json", allow_redirects=True
    )
    data = _decode_json_view(response.text)
    if data is None:
        return None

    error = str(data.get("error", ""))
    if "No user found" in error:
        return Result.available()

    if "is suspended" in error:
        return Result.error("Account suspended")

    payload = data.get("payload") or {}
    profile = payload.get("user") or {}
    # Medium resolves handles case-insensitively but reports canonical casing.
    username = str(profile.get("username", ""))
    if username.lower() != user.lower():
        return None

    extra: dict = {"username": username}
    for key, field in (("fullname", "name"), ("bio", "bio"), ("twitter", "twitterScreenName")):
        value = profile.get(field)
        if value:
            extra[key] = value

    user_id = profile.get("userId")
    if user_id:
        extra["id"] = user_id

    created_at = profile.get("createdAt")
    if created_at:
        joined = datetime.fromtimestamp(created_at / 1000, timezone.utc)
        extra["joined"] = joined.date().isoformat()

    # Keyed by user id, so the recommendation carousels that share `references`
    # cannot contribute their own counts.
    stats = ((payload.get("references") or {}).get("SocialStats") or {}).get(user_id) or {}
    for key, field in (("followers", "usersFollowedByCount"), ("following", "usersFollowedCount")):
        count = stats.get(field)
        if count is not None:
            extra[key] = count

    media = {}
    image_id = profile.get("imageId")
    if image_id:
        media["avatar"] = AVATAR_CDN + image_id

    return Result.taken(extra=extra, media=media)


def _decode_json_view(body: str) -> Optional[dict]:
    if JSON_GUARD not in body:
        return None
    try:
        data = json.loads(body.split(JSON_GUARD, 1)[1])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _from_profile_page(user: str) -> Optional[Result]:
    """The server-rendered profile. Accounts with a custom subdomain 301 to
    {user}.medium.com and only carry the markers after that hop; unknown handles
    never redirect.
    """
    response = impersonate_request(f"https://medium.com/@{user}", allow_redirects=True)
    html = response.text

    served = re.search(r'property="profile:username" content="([^"]*)"', html)
    if served and served.group(1).lower() == user.lower():
        extra = {"username": served.group(1)}
        media = {}

        person = _person_ld_json(html)
        name = person.get("name")
        if name:
            extra["fullname"] = name

        bio = person.get("description")
        if bio:
            extra["bio"] = bio

        # Anchored to this profile's own followers link — the sidebar carries
        # the same markup for recommended authors.
        followers = re.search(
            rf'href="/@{re.escape(served.group(1))}/followers[^"]*"[^>]*>([\d.,]+[KM]?)\s+followers',
            html,
        )
        if followers:
            extra["followers"] = followers.group(1)

        avatar = re.search(r'property="og:image" content="([^"]+)"', html)
        if avatar:
            media["avatar"] = avatar.group(1)

        return Result.taken(extra=extra, media=media)

    if any(marker in html for marker in NOT_FOUND_MARKERS):
        return Result.available()

    return None


def _person_ld_json(html: str) -> dict:
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Person":
            return data
    return {}


def _from_feed(user: str) -> Optional[Result]:
    """The story feed sits on a separate route, so it can answer when both
    profile views are blocked. Its 404 is not a miss — an account that has
    published nothing has no feed — so only a hit counts as a verdict.
    """
    response = impersonate_request(f"https://medium.com/feed/@{user}", allow_redirects=True)
    if response.status_code != 200:
        return None

    xml = response.text
    channel = re.search(
        rf"<link>https://medium\.com/@({re.escape(user)})\?source=rss", xml, re.IGNORECASE
    )
    if not channel:
        return None

    extra = {"username": channel.group(1)}
    name = re.search(r"<title><!\[CDATA\[Stories by (.*?) on Medium\]\]></title>", xml)
    if name:
        extra["fullname"] = name.group(1)

    media = {}
    avatar = re.search(r"<url>(https://cdn-images-1\.medium\.com/[^<]+)</url>", xml)
    if avatar:
        media["avatar"] = avatar.group(1)

    return Result.taken(extra=extra, media=media)
