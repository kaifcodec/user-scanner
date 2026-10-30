from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_donatealerts(user: str) -> Result:
    encoded_user = quote(user, safe="")
    url = f"https://www.donationalerts.com/api/v1/user/{encoded_user}/donationpagesettings"
    show_url = f"https://www.donationalerts.com/r/{encoded_user}"

    def process(response) -> Result:
        try:
            body = response.json()
        except Exception:
            return Result.error(f"Unexpected response body: HTTP {response.status_code}", url=show_url)

        if response.status_code == 200 and body.get("data"):
            data = body.get("data", {})
            extra: dict[str, str | int | bool] = {}
            media: dict[str, str] = {}

            if uid := data.get("id"):
                extra["id"] = uid
            if code := data.get("code"):
                extra["code"] = str(code)
            if name := data.get("name"):
                extra["name"] = str(name)
            if currency := data.get("preferred_currency"):
                extra["currency"] = str(currency)
            if (active := data.get("is_active")) is not None:
                extra["is_active"] = bool(active)
            if (verified := data.get("is_verified")) is not None:
                extra["is_verified"] = bool(verified)

            if goals := data.get("donation_goals", []):
                for goal in goals:
                    if goal.get("is_active") and goal.get("title"):
                        extra["active_goal"] = str(goal["title"])
                        if goal.get("goal_amount") is not None:
                            extra["goal_amount"] = f"{goal.get('raised_amount', 0)} / {goal['goal_amount']} {goal.get('currency', '')}".strip()
                        break

            if avatar := data.get("avatar"):
                media["avatar"] = str(avatar)
            if bg := data.get("background_image_url"):
                media["background"] = str(bg)

            return Result.taken(extra=extra, media=media, url=show_url)

        if (
            response.status_code in (202, 404)
            or not body.get("success", True)
            or body.get("code") == 1500
        ):
            return Result.available(url=show_url)

        return Result.error(f"Unexpected status {response.status_code}", url=show_url)

    return impersonate_validate(url, process, show_url=show_url)


# Backward-compatibility alias
validate_donation_alerts = validate_donatealerts
