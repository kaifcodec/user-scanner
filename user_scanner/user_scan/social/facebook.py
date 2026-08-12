import html
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

PROFILE_TITLE_RE = re.compile(r'<meta property="og:title" content="([^"]+)"')
PROFILE_URL_RE = re.compile(
    r'<meta property="og:url" content="(https://www\.facebook\.com/[^"]+)"'
)
DESCRIPTION_RE = re.compile(r'<meta property="og:description" content="([^"]*)"')
COUNTS_RE = re.compile(
    r"^.*?\.\s*(?P<likes>[\d,.]+) likes"
    r"(?:\s*&#xb7;\s*(?P<talking>[\d,.]+) talking about this)?\.\s*(?P<bio>.*)$",
    re.DOTALL,
)
# Facebook ships this error in two wordings ("at the moment" / "right now"),
# embedded in JSON where the apostrophe is backslash-escaped.
UNAVAILABLE_RE = re.compile(r"This content isn\\?'t available")


def validate_facebook(user: str) -> Result:
    if not (1 <= len(user) <= 50):
        return Result.error("Length must be 1-50 characters")

    if not re.match(r"^[a-zA-Z0-9.]+$", user):
        return Result.error("Only letters, numbers and periods allowed")

    if user.isdigit():
        return Result.error("Username cannot be numbers only")

    if user.startswith(".") or user.endswith("."):
        return Result.error("Username cannot start or end with a period")

    show_url = f"https://www.facebook.com/{user}"

    def process(response):
        return _process_profile_response(response.status_code, response.text)

    # A handle in non-canonical casing 302s to its canonical form; a miss does not.
    return impersonate_validate(show_url, process, show_url=show_url, allow_redirects=True)


def _process_profile_response(status_code: int, body: str) -> Result:
    if status_code == 429:
        return Result.error("Rate limited by Facebook")

    if status_code >= 500:
        return Result.error(f"Facebook returned HTTP {status_code}")

    title = PROFILE_TITLE_RE.search(body)
    canonical = PROFILE_URL_RE.search(body)
    has_unavailable_marker = bool(UNAVAILABLE_RE.search(body))

    if title and canonical and not has_unavailable_marker:
        return Result.taken(extra=_extract(title.group(1), canonical.group(1), body))

    if has_unavailable_marker and not (title and canonical):
        return Result.available()

    return Result.error("Unexpected response body, report it via GitHub issues.")


def _extract(title: str, canonical: str, body: str) -> dict:
    extra = {"name": html.unescape(title).strip()}

    # The canonical URL carries the handle's real casing, which the requested
    # one does not — Facebook resolves handles case-insensitively.
    handle = canonical.rsplit("/", 1)[-1]
    if handle:
        extra["handle"] = handle

    description = DESCRIPTION_RE.search(body)
    if not description:
        return extra

    counts = COUNTS_RE.match(description.group(1))
    if not counts:
        return extra

    extra["likes"] = counts.group("likes")
    if talking := counts.group("talking"):
        extra["talking_about"] = talking
    if bio := html.unescape(counts.group("bio")).strip():
        extra["bio"] = bio

    return extra
