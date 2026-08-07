import html
import re

from user_scanner.core.impersonate import impersonate_request
from user_scanner.core.result import Result

BASE_URL = "https://sourceforge.net"

# Cloudflare answers every other curl_cffi fingerprint (including the default
# "chrome") with a "Just a moment..." interstitial on this host; "safari184" is
# the only profile that reaches the origin. The same page comes back with 429
# once the host starts rate limiting, so it is matched on its title, not status.
IMPERSONATE = "safari184"

NOT_FOUND_TITLE = "Page not found - SourceForge.net"
MAX_LISTED_PROJECTS = 20


def validate_sourceforge(user: str) -> Result:
    if not (3 <= len(user) <= 30):
        return Result.error("Length must be 3-30 characters.")

    if not re.match(r"^[a-z0-9-]+$", user):
        if re.search(r"[A-Z]", user):
            return Result.error("Use lowercase letters only.")

        return Result.error("Only use lowercase letters, numbers, and dashes.")

    show_url = f"{BASE_URL}/u/{user}/profile/"

    try:
        response = impersonate_request(
            f"{BASE_URL}/rest/u/{user}/profile", impersonate=IMPERSONATE, allow_redirects=True
        )
    except Exception as e:
        return Result.error(e, url=show_url)

    if _is_challenge(response.text):
        return Result.error("Blocked by a Cloudflare challenge", url=show_url)

    if response.status_code == 404:
        if _title(response.text) == NOT_FOUND_TITLE:
            return Result.available(url=show_url)
        return Result.error("Unexpected 404 (not the not-found page)", url=show_url)

    if response.status_code != 200:
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    try:
        profile = response.json()
    except Exception:
        return Result.error("Profile endpoint did not return JSON", url=show_url)

    if str(profile.get("username", "")).lower() != user.lower():
        return Result.error("Profile confirmation not found", url=show_url)

    extra, media = _extract_page(user)
    extra.update(_extract_profile(profile))

    return Result.taken(extra=extra, media=media, url=show_url)


def _extract_page(user: str) -> tuple[dict, dict]:
    """Read the headline, latest activity and avatar, which the REST profile
    does not expose. Best effort: a failure here must not affect the verdict."""
    try:
        response = impersonate_request(
            f"{BASE_URL}/u/{user}/profile/", impersonate=IMPERSONATE, allow_redirects=True
        )
    except Exception:
        return {}, {}

    if response.status_code != 200 or _is_challenge(response.text):
        return {}, {}

    page = response.text
    extra: dict = {}
    media: dict = {}

    # The activity feed below repeats both the avatar and h2 markup for other
    # users, so the header block is the only safe place to read them from.
    header = _slice(page, '<div class="overview">', "</section>")

    headline = re.search(r'<h2 class="as-h3 summary">(.*?)</h2>', header, re.DOTALL)
    if headline:
        extra["headline"] = _text(headline.group(1))

    # The activity feed is ordered newest first.
    activity = re.search(r'<time datetime="([^"]+)"', page)
    if activity:
        extra["last_activity"] = activity.group(1)

    avatar = re.search(r'<img[^>]+src="([^"]*user_icon[^"]*)"', header)
    if avatar:
        media["avatar"] = html.unescape(avatar.group(1))

    return extra, media


def _extract_profile(profile: dict) -> dict:
    extra: dict = {}

    if profile.get("name"):
        extra["name"] = profile["name"]

    if profile.get("joined"):
        extra["joined"] = profile["joined"]

    localization = profile.get("localization") or {}
    location = ", ".join(
        part for part in (localization.get("city"), localization.get("country")) if part
    )
    if location:
        extra["location"] = location

    # The field defaults to "Unknown" for everyone who never set it.
    if profile.get("sex") and profile["sex"] != "Unknown":
        extra["sex"] = profile["sex"]

    if profile.get("webpages"):
        extra["webpages"] = ", ".join(profile["webpages"])

    if profile.get("telnumbers"):
        extra["phone_numbers"] = ", ".join(profile["telnumbers"])

    socials = "; ".join(
        f"{entry.get('socialnetwork')}: {entry.get('accounturl')}"
        for entry in profile.get("socialnetworks") or []
        if entry.get("accounturl")
    )
    if socials:
        extra["social_networks"] = socials

    skills = "; ".join(_format_skill(entry) for entry in profile.get("skills") or [])
    if skills:
        extra["skills"] = skills

    availability = "; ".join(
        f"{slot.get('week_day')} {slot.get('start_time')}-{slot.get('end_time')}"
        for slot in profile.get("availability") or []
    )
    if availability:
        extra["availability"] = availability

    projects = profile.get("projects") or []
    if projects:
        extra["projects"] = len(projects)
        names = [project.get("name", "") for project in projects[:MAX_LISTED_PROJECTS]]
        if len(projects) > MAX_LISTED_PROJECTS:
            names.append(f"(+{len(projects) - MAX_LISTED_PROJECTS} more)")
        extra["project_names"] = ", ".join(name for name in names if name)

    return extra


def _format_skill(entry: dict) -> str:
    skill = entry.get("skill") or {}
    name = skill.get("fullname") or skill.get("fullpath") or skill.get("shortname") or ""
    level = entry.get("level")
    return f"{name} ({level})" if name and level else name


def _is_challenge(page: str) -> bool:
    return _title(page) == "Just a moment..."


def _title(page: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", page, re.IGNORECASE | re.DOTALL)
    return _text(match.group(1)) if match else ""


def _slice(page: str, start_marker: str, end_marker: str) -> str:
    start = page.find(start_marker)
    if start < 0:
        return ""
    end = page.find(end_marker, start + len(start_marker))
    return page[start:end] if end > 0 else page[start:]


def _text(markup: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", markup))).strip()
