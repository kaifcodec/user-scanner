import json

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://unsplash.com"
# The site's own profile API. It answers with the full user object for a real
# handle and a distinct not-found payload otherwise, unlike the profile page,
# which is client-rendered and identical either way.
API_URL = f"{BASE_URL}/napi/users"
NOT_FOUND_MARKER = "Couldn't find User"

FIELDS = {
    "name": "name",
    "id": "id",
    "numeric_id": "numeric_id",
    "bio": "bio",
    "location": "location",
    "portfolio_url": "portfolio",
    "instagram_username": "instagram",
    "twitter_username": "twitter",
}
COUNTS = {
    "total_photos": "photos",
    "total_illustrations": "illustrations",
    "total_collections": "collections",
    "total_likes": "likes",
}


def validate_unsplash(user: str) -> Result:
    show_url = f"{BASE_URL}/@{user}"

    def process(response) -> Result:
        if response.status_code == 404 and NOT_FOUND_MARKER in response.text:
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        try:
            profile = json.loads(response.text)
        except json.JSONDecodeError:
            return Result.error("Malformed JSON response, report it on Github")

        if str(profile.get("username", "")).lower() != user.lower():
            return Result.error("Profile payload does not match the requested handle")

        return Result.taken(extra=_extract_profile(profile), media=_extract_media(profile))

    return impersonate_validate(
        f"{API_URL}/{user}", process, show_url=show_url, allow_redirects=True)


def _extract_profile(profile: dict) -> dict:
    extra: dict[str, str | bool | int] = {}

    for field, label in FIELDS.items():
        value = profile.get(field)
        if value in (None, ""):
            continue
        extra[label] = value if isinstance(value, (bool, int)) else str(value).strip()

    for field, label in COUNTS.items():
        value = profile.get(field)
        if isinstance(value, int):
            extra[label] = value

    badge = profile.get("badge") or {}
    if badge.get("title"):
        extra["badge"] = badge["title"]

    if profile.get("for_hire"):
        extra["for_hire"] = True

    downloads = _total_downloads(profile["username"])
    if downloads is not None:
        extra["downloads"] = downloads

    return extra


def _total_downloads(user: str) -> int | None:
    """The user object carries a `downloads` key that is 0 for every account;
    the real lifetime figure only comes from the statistics endpoint."""
    try:
        response = impersonate_request(
            f"{API_URL}/{user}/statistics", allow_redirects=True)
        if response.status_code != 200:
            return None
        total = json.loads(response.text).get("downloads", {}).get("total")
    except Exception:
        return None
    return total if isinstance(total, int) else None


def _extract_media(profile: dict) -> dict:
    images = profile.get("profile_image") or {}
    avatar = images.get("large") or images.get("medium") or images.get("small")
    return {"avatar": avatar} if avatar else {}
