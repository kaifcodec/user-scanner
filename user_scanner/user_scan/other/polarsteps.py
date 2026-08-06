from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_polarsteps(user: str) -> Result:
    encoded_user = quote(user, safe="")
    api_url = f"https://api.polarsteps.com/users/byusername/{encoded_user}"
    show_url = f"https://www.polarsteps.com/{encoded_user}"
    headers = {
        "Accept": "application/json",
        "Polarsteps-API-Version": "61",  # bump if module starts erroring on all lookups
    }

    def process(response):
        try:
            data = response.json()
        except ValueError:
            return Result.error(f"Unexpected non-JSON response: {response.status_code}")

        if not isinstance(data, dict):
            return Result.error("Unexpected response body")

        if data.get("error") == "api_version_too_old_for_endpoint":
            return Result.error(
                f"Polarsteps API version outdated — requires v{data.get('required_version')}, "
                f"update 'Polarsteps-API-Version' header in polarsteps.py"
            )

        if response.status_code == 404 and data == {"detail": "Not Found"}:
            return Result.available()

        if (
            response.status_code == 200
            and str(data.get("username", "")).casefold() == user.casefold()
        ):
            location = data.get("living_location") or {}
            stats = data.get("stats") or {}
            followers = data.get("followers")
            following = data.get("followees")
            visibility = data.get("visibility")
            extra = {
                "id": data.get("id"),
                "uuid": data.get("uuid"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "bio": data.get("description"),
                "joined": data.get("creation_date"),
                "locality": location.get("locality"),
                "administrative_area": location.get("administrative_area"),
                "country": location.get("country"),
                "country_code": location.get("country_code"),
                "is_private": visibility == 0 if visibility is not None else None,
                "subscription": data.get("subscription_type"),
                "followers": len(followers) if isinstance(followers, list) else None,
                "following": len(following) if isinstance(following, list) else None,
                "trips": stats.get("trip_count"),
                "steps": stats.get("step_count"),
                "countries": stats.get("country_count"),
                "continents": ", ".join(stats.get("continents") or []),
                "distance_km": stats.get("km_count"),
                "likes": stats.get("like_count"),
                "travel_seconds": stats.get("time_traveled_in_seconds"),
                "world_percentage": stats.get("world_percentage"),
                "last_trip_end": stats.get("last_trip_end_date"),
                "furthest_place": stats.get("furthest_place_from_home_location"),
                "furthest_country": stats.get("furthest_place_from_home_country"),
                "furthest_distance_km": stats.get("furthest_place_from_home_km"),
            }
            media = {"avatar": data.get("profile_image_path"),}
            return Result.taken(extra=extra, media=media)

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(api_url, process, headers=headers, show_url=show_url)
