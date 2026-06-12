from user_scanner.core.orchestrator import generic_validate, Result

def validate_discourse_meta(user):
    url = f"https://meta.discourse.org/u/{user}.json"
    show_url = f"https://meta.discourse.org/u/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            data = response.json()
            u = data.get("user", {})
            if u:
                extra = {}
                if u.get("id"): extra["id"] = u.get("id")
                if u.get("name"): extra["name"] = u.get("name")
                if u.get("username"): extra["username"] = u.get("username")
                if u.get("title"): extra["title"] = u.get("title")
                if u.get("last_posted_at"): extra["last_posted"] = u.get("last_posted_at")
                if u.get("last_seen_at"): extra["last_seen"] = u.get("last_seen_at")
                if u.get("created_at"): extra["registered"] = u.get("created_at")
                
                # Resolve avatar
                avatar = u.get("avatar_template")
                if avatar:
                    if "{size}" in avatar:
                        avatar = avatar.format(size=120)
                    if avatar.startswith("/"):
                        avatar = "https://meta.discourse.org" + avatar
                    extra["avatar"] = avatar
                    
                return Result.taken(extra=extra)
            return Result.available()
            
        raise Exception(f"Unexpected status code {response.status_code}")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
