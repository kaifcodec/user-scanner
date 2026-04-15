import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from user_scanner.core.result import Result

PROFILE_TITLE_RE = re.compile(r'<meta property="og:title" content="[^"]+"')
PROFILE_URL_RE = re.compile(
    r'<meta property="og:url" content="https://www\.facebook\.com/[^"]+"'
)
UNAVAILABLE_MARKER = "This content isn't available right now"


def _process_profile_response(status_code: int, html: str) -> Result:
    if status_code == 429:
        return Result.error("Rate limited by Facebook")

    if status_code >= 500:
        return Result.error(f"Facebook returned HTTP {status_code}")

    has_profile_markers = bool(
        PROFILE_TITLE_RE.search(html) and PROFILE_URL_RE.search(html)
    )
    has_unavailable_marker = UNAVAILABLE_MARKER in html

    if has_profile_markers and not has_unavailable_marker:
        return Result.taken()

    if has_unavailable_marker and not has_profile_markers:
        return Result.available()

    return Result.error("Unexpected response body, report it via GitHub issues.")


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
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    request = Request(show_url, headers=headers)

    try:
        with urlopen(request, timeout=8.0) as response:
            html = response.read().decode("utf-8", "ignore")
            return _process_profile_response(response.status, html).update(url=show_url)
    except HTTPError as exc:
        html = exc.read().decode("utf-8", "ignore")
        return _process_profile_response(exc.code, html).update(url=show_url)
    except URLError as exc:
        return Result.error(exc, url=show_url)
    except Exception as exc:
        return Result.error(exc, url=show_url)
