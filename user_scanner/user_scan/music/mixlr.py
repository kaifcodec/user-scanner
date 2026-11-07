import urllib.parse

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_mixlr(user: str) -> Result:
    encoded_user = urllib.parse.quote(user.lower())
    url = f"https://api.mixlr.com/users/{encoded_user}"
    show_url = f"https://mixlr.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            try:
                data = response.json()
                if data.get("error") == "Resource not found":
                    return Result.available()
            except Exception:
                pass
            if "Resource not found" in response.text:
                return Result.available()
            return Result.error("404 response received without expected error payload")

        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                return Result.error("Invalid JSON in 200 response")

            if not isinstance(data, dict) or "id" not in data:
                return Result.error("Unexpected API response structure")

            extra: dict[str, str] = {}
            media: dict[str, str] = {}

            if "id" in data:
                extra["id"] = str(data["id"])

            if role := data.get("role"):
                extra["role"] = str(role)

            if tz := data.get("time_zone"):
                extra["time_zone"] = str(tz)

            plan = data.get("plan") or {}
            if plan.get("reference"):
                extra["plan"] = str(plan["reference"])
            elif plan.get("name"):
                extra["plan"] = str(plan["name"])

            if data.get("is_premium"):
                extra["premium"] = "true"

            if data.get("is_live"):
                extra["live"] = "true"

            channel = data.get("channel") or {}
            if channel.get("name"):
                extra["channel"] = str(channel["name"])

            if avatar := data.get("profile_image_url"):
                if "fallback-user" not in avatar:
                    media["avatar"] = str(avatar)

            return Result.taken(extra=extra, media=media)

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
