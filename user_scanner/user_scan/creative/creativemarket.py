import json
import re
from html import unescape
from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


BASE_URL = "https://creativemarket.com/"
NOT_FOUND_MARKER = "Whoomp, there it isn&#039;t!"


def validate_creativemarket(user: str) -> Result:
    url = f"{BASE_URL}users/{quote(user, safe='')}"

    def process(response) -> Result:
        if response.status_code == 404:
            if NOT_FOUND_MARKER in response.text:
                return Result.available()
            return Result.error("Creative Market 404 response missing not-found marker")

        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        match = re.search(
            r"var _jsConfig = (\{.*?\});\s*var APP", response.text, re.DOTALL
        )
        if not match:
            return Result.error("Creative Market profile data not found")

        try:
            config = json.loads(match.group(1))
        except json.JSONDecodeError:
            return Result.error("Invalid Creative Market profile data")

        profile = config.get("pageData")
        if not isinstance(profile, dict) or config.get("page_type") != "user_activity":
            return Result.error("Unexpected Creative Market profile payload")

        username = profile.get("username")
        if not isinstance(username, str) or username.casefold() != user.casefold():
            return Result.error("Creative Market returned a different user")

        is_private = profile.get("isPrivate")
        extra = {
            "name": _profile_name(response.text, username),
            "bio": unescape(profile.get("userBio") or ""),
            "location": profile.get("userLocation"),
            "created": profile.get("userCreatedDate"),
            "followers": profile.get("numFollowers"),
            "following": profile.get("numFollowing"),
            "id": profile.get("userID"),
            "activity_public": not is_private if isinstance(is_private, bool) else None,
            "shop_owner": profile.get("shopExists"),
            "shop_title": profile.get("shopTitle"),
            "shop_rating": profile.get("shopReviewRating"),
            "shop_sales": profile.get("shopNumSales"),
        }
        for social in profile.get("socialLinks") or []:
            if isinstance(social, dict) and social.get("platform") and social.get("link"):
                extra[str(social["platform"]).lower()] = social["link"]

        return Result.taken(
            extra=extra,
            media={"avatar": profile.get("avatarUrl")},
        )

    return impersonate_validate(
        url,
        process,
        warmup_url=BASE_URL,
        allow_redirects=True,
    )


def _profile_name(document: str, username: str) -> str | None:
    match = re.search(
        rf"<title[^>]*>(.*?) \({re.escape(username)}\)\s*</title>",
        document,
        re.DOTALL | re.IGNORECASE,
    )
    return unescape(match.group(1)).strip() if match else None
