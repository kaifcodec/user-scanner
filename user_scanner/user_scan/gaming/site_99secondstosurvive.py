import urllib.parse

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_site_99secondstosurvive(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = "https://99secondstosurvive.miraheze.org/w/api.php"
    show_url = f"https://99secondstosurvive.miraheze.org/wiki/User:{encoded_user}"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "list": "users",
        "ususers": user,
        "usprop": "blockinfo|groups|editcount|registration|gender",
    }

    def process(response) -> Result:
        try:
            data = response.json()
            users = data.get("query", {}).get("users", [])
            if not users:
                return Result.error("MediaWiki response missing users list")

            user_data = users[0]
            if user_data.get("missing") is True:
                return Result.available(url=show_url)

            if "userid" in user_data:
                extra: dict[str, str] = {}
                extra["id"] = str(user_data["userid"])
                if user_data.get("registration"):
                    extra["joined"] = str(user_data["registration"])
                if user_data.get("editcount") is not None:
                    extra["edit_count"] = str(user_data["editcount"])
                if user_data.get("gender") and user_data.get("gender") != "unknown":
                    extra["gender"] = str(user_data["gender"])
                if user_data.get("groups"):
                    groups = [g for g in user_data["groups"] if g != "*"]
                    if groups:
                        extra["groups"] = ", ".join(groups)

                return Result.taken(url=show_url, extra=extra)
        except Exception:
            pass

        return Result.error(f"Unexpected response status {response.status_code}")

    return generic_validate(
        url,
        process,
        headers=headers,
        params=params,
        show_url=show_url,
        follow_redirects=True,
    )
