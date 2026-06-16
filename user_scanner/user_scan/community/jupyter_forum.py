from user_scanner.core.orchestrator import Result, make_request


def validate_jupyter_forum(user):
    url = f"https://discourse.jupyter.org/u/{user}.json"
    show_url = f"https://discourse.jupyter.org/u/{user}"
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}

    try:
        response = make_request(url, headers=headers)
        if response.status_code == 200:
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
                        avatar = "https://discourse.jupyter.org" + avatar
                    extra["avatar"] = avatar

                return Result.taken(extra=extra, url=show_url)
            return Result.available(url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(
                f"Unexpected status: {response.status_code}", url=show_url
            )
    except Exception as e:
        return Result.error(e, url=show_url)
