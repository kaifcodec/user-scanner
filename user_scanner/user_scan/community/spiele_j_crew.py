import urllib.parse

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_spiele_j_crew(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = "https://spiele.j-crew.de/w/api.php"
    show_url = f"https://spiele.j-crew.de/wiki/User:{encoded_user}"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }
    params = {
        "action": "query",
        "format": "json",
        "list": "users",
        "ususers": user,
        "usprop": "blockinfo|groups|editcount|registration|gender",
        "formatversion": "2",
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

            return Result.error("MediaWiki response missing userid and missing flag")
        except Exception as e:
            return Result.error(str(e))

    return generic_validate(
        url,
        process,
        headers=headers,
        params=params,
        show_url=show_url,
        follow_redirects=True,
    )
