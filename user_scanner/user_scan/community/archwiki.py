from user_scanner.core.orchestrator import Result, generic_validate


def validate_archwiki(user):
    url = f"https://wiki.archlinux.org/api.php?action=query&format=json&list=users&ususers={user}&usprop=cancreate&formatversion=2"
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
                return Result.taken()
            
            return Result.error("Unexpected user structure")
        except Exception as e:
            return Result.error(e)
    return generic_validate(url, process, show_url=show_url)
