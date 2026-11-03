from user_scanner.core.orchestrator import generic_validate, Result
from user_scanner.core.helpers import get_random_user_agent


def validate_destream(user: str) -> Result:
    url = f"https://api.destream.net/siteapi/v2/live/details/{user}"
    show_url = f"https://destream.net/live/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response) -> Result:
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get("userName"):
                    extra: dict[str, str] = {"username": str(data["userName"])}
                    media: dict[str, str] = {}
                    if avatar := data.get("logoImageUrl"):
                        media["avatar"] = str(avatar)
                    if stream := data.get("liveStream"):
                        extra["live_stream"] = str(stream)
                    if channel := data.get("channel"):
                        extra["channel"] = str(channel)
                    return Result.taken(extra=extra, media=media)
            except Exception:
                pass
            return Result.error("200 response status with no recognizable data")

        if response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url)
