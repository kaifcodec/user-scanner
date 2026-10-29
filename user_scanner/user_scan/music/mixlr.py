from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_mixlr(user: str) -> Result:
    url = f"https://api.mixlr.com/users/{user.lower()}"
    show_url = f"https://mixlr.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()

        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                return Result.error("200 response status with no recognizable data, report it via GitHub issues")
            if not isinstance(data, dict) or "id" not in data or "slug" not in data:
                return Result.error("Unexpected API response body, report it via GitHub issues")

            extra = {}
            media = {}
            if username := data.get("username"): extra["username"] = username
            if slug := data.get("slug"): extra["slug"] = slug
            if role := data.get("role"): extra["role"] = role
            if tz := data.get("time_zone"): extra["time_zone"] = tz
            plan = data.get("plan") or {}
            if plan.get("reference"): extra["plan"] = plan["reference"]
            elif plan.get("name"): extra["plan"] = plan["name"]
            if data.get("is_premium"): extra["premium"] = "true"
            if data.get("is_live"): extra["live"] = "true"
            channel = data.get("channel") or {}
            if channel.get("name"): extra["channel"] = channel["name"]
            if avatar := data.get("profile_image_url"):
                if "fallback-user" not in avatar: media["avatar"] = avatar

            return Result.taken(extra=extra, media=media)

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
