from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

API_URL = "https://be-lb-app.scaleabout.com/api/v1"


def validate_wisio(user: str) -> Result:
    show_url = f"https://www.wisio.com/{user}"

    def process_availability(response):
        available = response.text.strip()
        if response.status_code != 200 or available not in {"true", "false"}:
            return Result.error(
                f"Unexpected Wisio availability response: {response.status_code}"
            )
        if available == "true":
            return Result.available()

        def process_profile(profile_response):
            if profile_response.status_code == 404:
                return Result.error(
                    "No public creator profile "
                    "(private, reserved, and invalid usernames look the same)"
                )

            if profile_response.status_code != 200:
                return Result.error(
                    f"Unexpected Wisio profile response: {profile_response.status_code}"
                )
            profile = profile_response.json()

            username = profile.get("username") if isinstance(profile, dict) else None
            if not isinstance(username, str) or username.casefold() != user.casefold():
                return Result.error(
                    "Wisio profile did not match the requested username"
                )

            skills = [
                skill["name"]
                for skill in profile.get("skills") or []
                if isinstance(skill, dict) and isinstance(skill.get("name"), str)
            ]
            social_links = [
                channel.get("formatted_url") or channel.get("url")
                for channel in profile.get("social_channels") or []
                if isinstance(channel, dict)
                and isinstance(channel.get("formatted_url") or channel.get("url"), str)
            ]
            external_links = [
                link["url"]
                for link in profile.get("links") or []
                if isinstance(link, dict) and isinstance(link.get("url"), str)
            ]
            avatar = profile.get("avatar") or {}
            cover = profile.get("cover_image") or {}

            return Result.taken(
                extra={
                    "id": profile.get("id"),
                    "first_name": profile.get("first_name"),
                    "last_name": profile.get("last_name"),
                    "display_name": profile.get("display_name"),
                    "title": profile.get("title"),
                    "location": profile.get("location"),
                    "skills": skills or None,
                    "social_links": social_links or None,
                    "external_links": external_links or None,
                    "reviews": profile.get("reviews_count"),
                    "rating": profile.get("reviews_score"),
                    "created_at": profile.get("created_at"),
                    "updated_at": profile.get("updated_at"),
                    "preferred_currency": profile.get("preferred_currency"),
                    "seller_availability": profile.get("seller_availability"),
                    "locale": profile.get("locale"),
                    "vacation": profile.get("vacation"),
                },
                media={
                    "avatar": (avatar.get("medium") or {}).get("url")
                    if isinstance(avatar, dict)
                    else None,
                    "cover": (cover.get("big") or {}).get("url")
                    if isinstance(cover, dict)
                    else None,
                },
            )

        return generic_validate(
            f"{API_URL}/users/{quote(user, safe='')}",
            process_profile,
        )

    return generic_validate(
        f"{API_URL}/users/is_username_allowed",
        process_availability,
        params={"username": user},
        show_url=show_url,
    )
