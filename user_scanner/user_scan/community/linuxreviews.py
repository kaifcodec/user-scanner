import urllib.parse

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_linuxreviews(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = "https://linuxreviews.org/w/api.php"
    show_url = f"https://linuxreviews.org/wiki/User:{encoded_user}"
    data = {
        "action": "query",
        "format": "json",
        "list": "users",
        "ususers": user,
        "usprop": "blockinfo|groups|editcount|registration|gender",
        "formatversion": "2",
    }

    def process(response) -> Result:
        try:
            res_data = response.json()
            users = res_data.get("query", {}).get("users", [])
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

    return impersonate_validate(
        url,
        process,
        method="POST",
        data=data,
        show_url=show_url,
        allow_redirects=True,
    )
