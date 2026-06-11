from user_scanner.core.orchestrator import generic_validate, Result


def validate_bitchute(user):
    url = "https://api.bitchute.com/api/beta/channel"
    show_url = f"https://www.bitchute.com/channel/{user}/"
    payload = {"channel_id": user}
    headers = {"Content-Type": "application/json"}

    def process(response):
        if '"channel_id":' in response.text:
            extra = {}
            try:
                data = response.json()
                if "channel_name" in data:
                    extra["name"] = data["channel_name"]
                if "description" in data and data["description"]:
                    extra["description"] = data["description"].strip()
                if "subscriber_count" in data:
                    extra["subscribers"] = data["subscriber_count"]
                if "video_count" in data:
                    extra["videos"] = data["video_count"]
            except Exception:
                pass
            return Result.taken(extra=extra)

        if '"errors":' in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, method="post", json=payload, headers=headers, show_url=show_url)
