from user_scanner.core.orchestrator import Result, generic_validate


def validate_picsart(user: str) -> Result:
    url = f"https://api.picsart.com/users/show/{user}.json"
    show_url = f"https://picsart.com/u/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("status") == "success":
                    extra: dict[str, str | int | bool] = {}
                    media: dict[str, str] = {}

                    if data.get("id"):
                        extra["id"] = data.get("id")
                    if data.get("name"):
                        extra["name"] = data.get("name")
                    if data.get("status_message"):
                        extra["status_message"] = data.get("status_message")
                    if data.get("followers_count") is not None:
                        extra["followers"] = data.get("followers_count")
                    if data.get("following_count") is not None:
                        extra["following"] = data.get("following_count")
                    if data.get("likes_count") is not None:
                        extra["likes"] = data.get("likes_count")
                    if data.get("photos_count") is not None:
                        extra["photos"] = data.get("photos_count")
                    if data.get("stickers_count") is not None:
                        extra["stickers"] = data.get("stickers_count")
                    if data.get("video_count") is not None:
                        extra["videos"] = data.get("video_count")
                    if data.get("tags_count") is not None:
                        extra["tags_count"] = data.get("tags_count")
                    if data.get("tags"):
                        extra["tags"] = ", ".join(data.get("tags", []))
                    if data.get("is_verified") is not None:
                        extra["is_verified"] = bool(data.get("is_verified"))

                    if data.get("photo"):
                        media["avatar"] = data.get("photo")
                    if data.get("cover"):
                        media["cover"] = data.get("cover")

                    return Result.taken(extra=extra, media=media, url=show_url)

                if data.get("reason") == "user_not_found" or data.get("message") == "User not found":
                    return Result.available(url=show_url)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available(url=show_url)

        return Result.error("Unexpected response body, report it via GitHub issues.", url=show_url)

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    return generic_validate(url, process, show_url=show_url, headers=headers)
