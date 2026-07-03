from user_scanner.core.orchestrator import Result, generic_validate


def validate_f_droid(user):
    url = f"https://forum.f-droid.org/u/{user}.json"
    show_url = f"https://forum.f-droid.org/u/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            data = response.json()
            u = data.get("user", {})
            if u:
                extra = {
                    "id": u.get("id"),
                    "name": u.get("name"),
                    "username": u.get("username"),
                    "title": u.get("title"),
                    "last_posted": u.get("last_posted_at"),
                    "last_seen": u.get("last_seen_at"),
                    "registered": u.get("created_at"),
                }

                # Resolve avatar
                avatar = u.get("avatar_template")
                if avatar:
                    if "{size}" in avatar:
                        avatar = avatar.format(size=120)
                    if avatar.startswith("/"):
                        avatar = "https://forum.f-droid.org" + avatar
                    extra["avatar"] = avatar

                return Result.taken(extra=extra)

        return Result.error(f"Unexpected response status: {response.status_code}")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
