from user_scanner.core.orchestrator import Result, generic_validate


def validate_archwiki(user):
    url = f"https://wiki.archlinux.org/api.php?action=query&format=json&list=users&ususers={user}&usprop=blockinfo|groups|editcount|registration|gender&formatversion=2"
    show_url = f"https://wiki.archlinux.org/title/User:{user}"

    def process(response):
        try:
            data = response.json()
            users = data.get("query", {}).get("users", [])
            if not users:
                return Result.available()
            
            user_data = users[0]
            if user_data.get("missing") is True:
                return Result.available()
            if "userid" in user_data:
                extra = {}
                try:
                    extra["id"] = user_data.get("userid")
                    if "registration" in user_data:
                        extra["joined"] = user_data.get("registration")
                    if "editcount" in user_data:
                        extra["edit_count"] = user_data.get("editcount")
                    if "gender" in user_data and user_data.get("gender") != "unknown":
                        extra["gender"] = user_data.get("gender")
                    if "groups" in user_data:
                        # Exclude general wildcard group if it's there
                        groups = [g for g in user_data.get("groups", []) if g != "*"]
                        if groups:
                            extra["groups"] = ", ".join(groups)
                except Exception:
                    pass
                return Result.taken(extra=extra)
            
            return Result.error("Unexpected user structure")
        except Exception as e:
            return Result.error(e)
    return generic_validate(url, process, show_url=show_url)
