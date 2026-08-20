import re
from datetime import datetime, timezone

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.nextjs import (
    parse_next_pages_data,
    parse_next_pages_redirect,
)
from user_scanner.core.result import Result

LANDING_MARKER = '<meta property="og:url" content="https://throne.com/landing">'
USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{3,50}$")


def validate_throne(user: str) -> Result:
    if not USERNAME_RE.fullmatch(user):
        return Result.error(
            "Username must be 3-50 letters, numbers, hyphens, or underscores."
        )

    url = f"https://throne.com/{user}"

    def process(response):
        if response.status_code == 307 and response.headers.get("location") == "/":
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        if LANDING_MARKER in response.text:
            return Result.available()

        data = parse_next_pages_data(response.text) or {}
        page_props = data["props"]["pageProps"]
        # An uncached slug returns an empty shell before Next.js resolves it.
        # Fetch the final profile or not-found result as the browser does.
        if data.get("isFallback"):
            data_response = impersonate_request(
                f"https://throne.com/_next/data/{data['buildId']}/{user}.json",
                headers={"x-nextjs-data": "1"},
            )
            data_response.raise_for_status()
            page_props = data_response.json()["pageProps"]
            # Missing profiles are 307 home redirects in 200 JSON, not HTTP redirects.
            if parse_next_pages_redirect(page_props) == ("/", 307):
                return Result.available()

        fallback = page_props.get("fallback") or {}
        profile = fallback.get(f"$sub$public/useCreatorByUsername/{user}", {})
        if profile.get("username") != user:
            return Result.error("Profile markers did not match the requested username")

        return Result.taken(extra=_extract(profile), media=_media(profile))

    return impersonate_validate(url, process)


def _extract(profile: dict) -> dict:
    extra: dict[str, object] = {"username": profile["username"]}
    for source, target in (
        ("_id", "id"),
        ("displayName", "fullname"),
        ("bio", "bio"),
        ("creatorType", "creator_type"),
        ("mainContentPlatform", "main_platform"),
        ("isPartner", "partner"),
        ("isNSFW", "nsfw"),
    ):
        if source in profile and profile[source] not in (None, ""):
            extra[target] = profile[source]

    for source, target in (("createdAt", "joined"), ("updatedAt", "updated")):
        timestamp = profile.get(source)
        if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
            extra[target] = datetime.fromtimestamp(
                timestamp / 1000, timezone.utc
            ).isoformat(timespec="milliseconds")

    interests = profile.get("interests")
    if isinstance(interests, list) and interests:
        extra["interests"] = interests

    for link in profile.get("socialLinks") or []:
        if isinstance(link, dict) and link.get("type") and link.get("url"):
            extra[link["type"]] = link["url"]

    return extra


def _media(profile: dict) -> dict:
    return {
        target: profile[source]
        for source, target in (
            ("pictureUrl", "avatar"),
            ("backgroundPictureUrl", "banner"),
        )
        if profile.get(source)
    }
