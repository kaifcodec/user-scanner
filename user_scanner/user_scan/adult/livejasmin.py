import re
import json
import html
import threading

from user_scanner.core.impersonate import impersonate_request
from user_scanner.core.result import Result

BASE_URL = "https://www.livejasmin.com"
SIGNUP_URL = f"{BASE_URL}/en/auth/sign-up"
# The signup form's live nick check. Performers are a separate namespace and read
# as free here, so it only settles plain member accounts.
CHECK_URL = f"{BASE_URL}/en/auth/validate/check-nick"
CHECK_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": SIGNUP_URL,
    "Origin": BASE_URL,
}

_token_lock = threading.Lock()
_form_token: str | None = None

# Fields from the embedded player config, mapped to friendlier extra keys.
CONFIG_FIELDS = {
    "display_name": "name",
    "pid": "user_id",
    "supercategory": "category",
    "subcategory": "age_group",
    "tags": "tags",
    "lastonlineat": "last_online",
}


def validate_livejasmin(user: str) -> Result:
    show_url = f"{BASE_URL}/en/chat/{user}"

    try:
        response = impersonate_request(show_url, allow_redirects=True)
    except Exception as e:
        return Result.error(e, url=show_url)

    if response.status_code != 200:
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    # Both states answer 200, so the body decides. A real performer page carries
    # the performerName meta; it persists while the model is offline, so it is an
    # existence signal rather than a live-stream one.
    performer = _meta(response.text, "performerName")
    if performer and performer.lower() == user.lower():
        extra = {"type": "performer", **_extract_profile(response.text)}
        return Result.taken(extra=extra, url=show_url)

    # The miss page is titled "<handle> is not available". Not being a performer
    # says nothing about member accounts, which have no public page at all, so
    # the signup name check decides those.
    if performer or f"{user.lower()} is not available" not in _title(response.text).lower():
        return Result.error("Profile confirmation not found", url=show_url)

    return _member_account(user, show_url)


def _member_account(user: str, show_url: str) -> Result:
    """Members own no public page; the signup form's nick check is the only
    public existence signal. Performers read as free here, hence the caller
    rules them out first."""
    try:
        payload = _check_nick(user)
        if payload is None:
            return Result.error("Name check gave no response", url=show_url)

        if payload.get("success") is True:
            return Result.available(url=show_url)

        # `errors` is reused for taken names and for rejected input ("too
        # short", "too long"), so only the message separates them.
        errors = str(payload.get("errors", "")).strip()
        if "already exists" in errors.lower():
            return Result.taken(extra={"type": "member"}, url=show_url)

        return Result.error(errors or "Name check gave no verdict", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)


def _check_nick(user: str) -> dict | None:
    # A stale form token yields a non-JSON body; refetch once before giving up.
    for refresh in (False, True):
        token = _signup_token(refresh)
        if not token:
            return None
        response = impersonate_request(
            CHECK_URL, method="POST", data={"nick": user, "csrfToken": token},
            headers=CHECK_HEADERS, allow_redirects=True)
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            continue
    return None


def _signup_token(refresh: bool = False) -> str | None:
    # One token serves every lookup in a run, so it is fetched once and shared.
    global _form_token
    with _token_lock:
        if _form_token and not refresh:
            return _form_token
        response = impersonate_request(SIGNUP_URL, allow_redirects=True)
        match = re.search(r'name="form_token"[^>]*value="([^"]+)"', response.text)
        _form_token = match.group(1) if match else None
        return _form_token


def _extract_profile(html_text: str) -> dict:
    extra = {}

    # The player bootstrap config holds the profile details as a flat JS object.
    for key, label in CONFIG_FIELDS.items():
        match = re.search(rf'"{key}":\s*"([^"]*)"|"{key}":\s*(\d+)', html_text, re.IGNORECASE)
        if not match:
            continue
        value = (match.group(1) or match.group(2) or "").strip()
        if value:
            extra[label] = html.unescape(value)

    avatar = _meta(html_text, "og:image")
    # The miss page falls back to a static site banner; only keep real snapshots.
    if avatar and "seo_og" not in avatar:
        extra["avatar"] = avatar

    return extra


def _meta(html_text: str, name: str) -> str | None:
    match = re.search(
        rf'<meta[^>]+(?:name|property)="{re.escape(name)}"[^>]+content="([^"]*)"',
        html_text, re.IGNORECASE)
    return html.unescape(match.group(1)).strip() if match else None


def _title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    return html.unescape(match.group(1)).strip() if match else ""
