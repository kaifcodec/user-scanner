import re
import json
import html

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://www.xnxx.com"

# The signup form's live name check. It answers for every registered account,
# including plain members, who get no public page anywhere on XNXX.
CHECK_URL = f"{BASE_URL}/account/checkprofilename"
HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/account/create",
}

# /pornstar/ resolves both public account kinds; the embedded user object's own
# `url` field names the namespace the account really belongs to.
ACCOUNT_TYPES = {"pornstar": "model", "porn-maker": "porn_maker"}


def validate_xnxx(user: str) -> Result:
    show_url = f"{BASE_URL}/pornstar/{user}"

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        try:
            payload = json.loads(response.text)
        except json.JSONDecodeError:
            return Result.error("Name check response was not JSON", url=show_url)

        if payload.get("result") is True:
            return Result.available(url=show_url)

        # `code` is 1 both for a taken name and for a rejected one ("too short",
        # "is not allowed"), so only the message separates them.
        message = html.unescape(str(payload.get("message", ""))).strip()
        if "already exists" not in message.lower():
            return Result.error(message or "Name check gave no verdict", url=show_url)

        return Result.taken(extra=_public_profile(user), url=show_url)

    return impersonate_validate(
        CHECK_URL, process, show_url=show_url, params={"profile": user}, headers=HEADERS
    )


def _public_profile(user: str) -> dict:
    """Registered names only get a public page when they are a model or an
    uploader; plain members have none. Best-effort: a miss just means the
    account exists without anything public to show."""
    try:
        response = impersonate_request(f"{BASE_URL}/pornstar/{user}", allow_redirects=True)
        if response.status_code != 200:
            return {"type": "member"}
    except Exception:
        return {"type": "member"}

    user_obj = _user_object(response.text)
    if user_obj.get("username", "").lower() != user.lower():
        return {"type": "member"}

    return _extract_profile(response.text, user_obj)


def _extract_profile(html_text: str, user_obj: dict) -> dict:
    extra = {}

    namespace = re.match(r"/([^/]+)/", user_obj.get("url") or "")
    if namespace:
        extra["type"] = ACCOUNT_TYPES.get(namespace.group(1), namespace.group(1))

    if user_obj.get("display"):
        extra["name"] = user_obj["display"]
    if user_obj.get("id_user"):
        extra["user_id"] = str(user_obj["id_user"])
    if user_obj.get("sex"):
        extra["gender"] = user_obj["sex"]
    avatar = user_obj.get("profile_picture") or user_obj.get("profile_picture_small")
    if avatar:
        extra["avatar"] = avatar

    aliases = _aliases(html_text, user_obj.get("display", ""))
    if aliases:
        extra["aliases"] = ", ".join(aliases)

    return extra


def _user_object(html_text: str) -> dict:
    # Same embedded JSON `user` object as xvideos (same operator); the `url`
    # field comes last, so match up to it and parse the whole object.
    match = re.search(r'"user":(\{.*?"url":"[^"]*"\})', html_text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def _aliases(html_text: str, display: str) -> list[str]:
    # The meta description leads with the model's names, then boilerplate:
    # "Dave Flores,David Bainer,free videos, latest updates and direct chat".
    match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', html_text, re.IGNORECASE)
    if not match:
        return []

    names, _, _ = html.unescape(match.group(1)).partition(",free videos")
    seen = []
    for name in names.split(","):
        name = name.strip()
        if name and name.lower() != display.lower() and name not in seen:
            seen.append(name)
    return seen
