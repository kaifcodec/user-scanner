from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_wiktionary(user: str) -> Result:
    url = "https://en.wiktionary.org/w/api.php"
    show_url = f"https://en.wiktionary.org/wiki/User:{user}"
    params = {
        "action": "query",
        "format": "json",
        "list": "users",
        "ususers": user,
        "usprop": "blockinfo|groups|editcount|registration|gender",
        "formatversion": 2,
    }

    def process(response) -> Result:
        try:
            data = response.json()
            users = data.get("query", {}).get("users", [])
            if not users:
                return Result.available(url=show_url)

            user_data = users[0]
            if user_data.get("missing") is True:
                return Result.available(url=show_url)

            if "userid" in user_data:
                extra: dict[str, object] = {}
                extra["id"] = user_data.get("userid")
                if "registration" in user_data and user_data.get("registration"):
                    extra["joined"] = user_data.get("registration")
                if "editcount" in user_data and user_data.get("editcount") is not None:
                    extra["edit_count"] = user_data.get("editcount")
                if "gender" in user_data and user_data.get("gender") not in ("unknown", None):
                    extra["gender"] = user_data.get("gender")
                if "groups" in user_data:
                    groups = [g for g in user_data.get("groups", []) if g != "*"]
                    if groups:
                        extra["groups"] = ", ".join(groups)
                return Result.taken(extra=extra if extra else None, url=show_url)

            return Result.error("Unexpected MediaWiki user structure", url=show_url)
        except Exception as e:
            return Result.error(e, url=show_url)

    return impersonate_validate(url, process, show_url=show_url, params=params)
