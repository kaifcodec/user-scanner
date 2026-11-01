from user_scanner.core.orchestrator import generic_validate, Result


def validate_bitchute(user: str) -> Result:
    url = "https://api.bitchute.com/api/beta/channel"
    show_url = f"https://www.bitchute.com/channel/{user}/"
    payload = {"channel_id": user}
    headers = {"Content-Type": "application/json"}

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, str | int] = {}
            media: dict[str, str] = {}
            try:
                data = response.json()
                if isinstance(data, dict) and ("channel_id" in data or "channel_name" in data):
                    if data.get("channel_name"):
                        extra["name"] = data["channel_name"]
                    if data.get("description"):
                        extra["description"] = data["description"].strip()
                    if data.get("subscriber_count") is not None:
                        extra["subscribers"] = data["subscriber_count"]
                    if data.get("video_count") is not None:
                        extra["videos"] = data["video_count"]
                    if data.get("view_count") is not None:
                        extra["views"] = data["view_count"]
                    if data.get("thumbnail_url"):
                        media["avatar"] = data["thumbnail_url"]
                    return Result.taken(extra=extra, media=media)
            except Exception:
                pass

        if response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, method="post", json=payload, headers=headers, show_url=show_url)
