import base64

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result

WARMUP_URL = "https://www.tripadvisor.com/"
GRAPHQL_URL = "https://www.tripadvisor.com/data/graphql/ids"

# TripAdvisor renders the profile client-side, so name/hometown/bio/etc. are not
# in the page HTML — they come from this persisted GraphQL query. The id is
# registered server-side by TripAdvisor and can change when they redeploy; if it
# does, metadata degrades to empty while found/available detection keeps working.
PROFILE_QUERY_ID = "b7f6eb32ff629f60"


def validate_tripadvisor(user: str) -> Result:
    url = f"https://www.tripadvisor.com/Profile/{user}"

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available()

        if response.status_code == 200:
            if "<title>404 Not Found" in response.text or 'name="robots" content="noindex"' in response.text:
                return Result.available()

            profile, extra, media = _fetch_profile(user)
            if isinstance(profile, dict):
                if str(profile.get("username", "")).casefold() == user.casefold():
                    return Result.taken(extra=extra, media=media)
                return Result.available()

            if profile is False:
                return Result.available()

            return Result.taken(extra=extra, media=media)

        # Handles are case-canonicalized: a non-canonical casing 301-redirects
        # to the real profile, so a redirect back to /Profile/ still means the
        # account exists. Only a genuinely missing handle returns 404.
        if response.status_code in (301, 302):
            location = response.headers.get("location", "")
            if "/profile/" in location.lower():
                profile, extra, media = _fetch_profile(user)
                if isinstance(profile, dict):
                    if str(profile.get("username", "")).casefold() == user.casefold():
                        return Result.taken(extra=extra, media=media)
                    return Result.available()
                if profile is False:
                    return Result.available()
                return Result.taken(extra=extra, media=media)

        return Result.error(f"Unexpected status: {response.status_code}")

    return impersonate_validate(url, process, warmup_url=WARMUP_URL, show_url=url)


def _fetch_profile(user: str) -> tuple[dict | bool | None, dict, dict]:
    payload = [
        {
            "variables": {"username": user},
            "extensions": {"preRegisteredQueryId": PROFILE_QUERY_ID},
        }
    ]
    # Metadata is best-effort: a parsing failure must never turn a found
    # account into an error, so the whole enrichment is guarded.
    try:
        response = impersonate_request(
            GRAPHQL_URL, method="POST", warmup_url=WARMUP_URL, json=payload
        )
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and "data" in data[0]:
                profiles = data[0]["data"].get("memberProfiles")
                if profiles and profiles[0] and isinstance(profiles[0], dict):
                    profile = profiles[0]
                    extra, media = _parse_profile(profile)
                    return profile, extra, media
                if profiles == [None] or profiles == []:
                    return False, {}, {}
    except Exception:
        pass
    return None, {}, {}


def _parse_profile(profile: dict) -> tuple[dict, dict]:
    sizes = (profile.get("avatar") or {}).get("photoSizes") or []
    avatar = max(sizes, key=lambda p: p.get("width") or 0).get("url") if sizes else None

    return (
        {
            "name": profile.get("displayName"),
            "user_id": profile.get("userId"),
            "bio": profile.get("bio"),
            "joined": profile.get("created"),
            "hometown": _extract_hometown(profile),
            "website": _decode_website(profile.get("website")),
            "verified": profile.get("isVerified"),
        },
        {
            "avatar": avatar,
        },
    )


def _extract_hometown(profile: dict) -> str | None:
    # Nested fields can be present-but-null, so coalesce with `or {}` at each
    # hop rather than relying on .get() defaults (which a null value bypasses).
    hometown = profile.get("hometown") or {}
    location = hometown.get("location") or {}
    long_name = (location.get("additionalNames") or {}).get("long")
    if long_name:
        return long_name
    # No resolved location: fall back to the free-text hometown, unless it is
    # just the numeric locationId echoed back as a string.
    fallback = hometown.get("fallbackString")
    if fallback and not fallback.isdigit():
        return fallback
    return None


def _decode_website(encoded: str | None) -> str | None:
    if not encoded:
        return None
    try:
        decoded = base64.b64decode(encoded).decode("utf-8", "replace")
    except Exception:
        return None
    # TripAdvisor wraps the real URL as <rand>_<url>_<rand>; drop both wrappers.
    inner = decoded.split("_", 1)[-1].rsplit("_", 1)[0].strip()
    return inner if inner.startswith(("http://", "https://")) else None
