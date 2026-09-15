from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_cameo(user: str) -> Result:
    encoded_user = quote(user, safe="")
    api_url = f"https://www.cameo.com/api/v2/users/{encoded_user}"
    profile_url = f"https://www.cameo.com/{encoded_user}"

    def process(response) -> Result:
        profile = response.json()

        if response.status_code == 404 and profile.get("message", "").startswith(
            "We could not find the user:"
        ):
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected Cameo response: {response.status_code}")

        username = profile.get("username")
        if not isinstance(username, str) or username.casefold() != user.casefold():
            return Result.error("Cameo profile did not match the requested username")

        reviews = profile.get("reviews") or {}
        categories = profile.get("categories") or []
        socials = profile.get("socials") or []
        core = (profile.get("products") or {}).get("core") or {}
        bookings = core.get("bookings") or {}
        image = profile.get("imageUrlKey")

        return Result.taken(
            extra={
                "uid": profile.get("_id"),
                "name": profile.get("name"),
                "profession": (profile.get("profession") or "").strip() or None,
                "bio": profile.get("bio"),
                "status": profile.get("status"),
                "created_at": profile.get("createdAt"),
                "birthday": profile.get("birthday"),
                "last_booked_at": core.get("lastBookedAt"),
                "last_completed_at": core.get("lastCompletedAt"),
                "bookings_last_24_hours": bookings.get("last24Hours"),
                "bookers_last_24_hours": bookings.get("last24HoursBookers"),
                "bookings_last_week": bookings.get("lastWeek"),
                "bookings_last_6_months": bookings.get("last6Months"),
                "rating": reviews.get("rating"),
                "reviews": reviews.get("count"),
                "categories": [item["name"] for item in categories if item.get("name")]
                or None,
                "links": [item["url"] for item in socials if item.get("url")]
                or None,
            },
            media={
                "avatar": image and f"https://cdn2.cameo.com/resizer/{image}",
                "intro_thumbnail": (profile.get("intro") or {}).get("thumbnailUrl"),
            },
        )

    return generic_validate(
        api_url, process, show_url=profile_url, headers={"Accept": "application/json"}
    )
