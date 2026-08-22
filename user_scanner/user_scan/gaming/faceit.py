import json
from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_faceit(user: str) -> Result:
    """Validate a player handle on Faceit (faceit.com)."""
    url = f"https://www.faceit.com/api/users/v1/nicknames/{user}"
    show_url = f"https://www.faceit.com/en/players/{user}"
    headers = {
        "Accept": "application/json",
    }

    def process(response):
        # 1. Explicit verification of available / not-found state
        if response.status_code == 404 or "user not found" in response.text.lower():
            return Result.available(url=show_url)

        # 2. Explicit verification of 200 OK + Faceit user payload
        if response.status_code == 200 and '"result":"OK"' in response.text.replace(" ", ""):
            try:
                data = json.loads(response.text)
                payload = data.get("payload", {})
                if payload and (payload.get("nickname") or "").lower() == user.lower():
                    extra = {}
                    media = {}

                    if nickname := payload.get("nickname"):
                        extra["nickname"] = str(nickname).strip()
                    if user_id := payload.get("id"):
                        extra["user_id"] = str(user_id).strip()
                    if country := payload.get("country"):
                        extra["country"] = str(country).strip().upper()
                    if created_at := payload.get("created_at"):
                        extra["created_at"] = str(created_at).strip()
                    if verified := payload.get("verified"):
                        extra["verified"] = str(verified)

                    # Extract linked platform accounts (Steam, Twitch)
                    platforms = payload.get("platforms", {})
                    if steam := platforms.get("steam", {}):
                        if steam_id := steam.get("id64"):
                            extra["steam_id64"] = str(steam_id)

                    streaming = payload.get("streaming", {})
                    if twitch_id := streaming.get("twitch_id"):
                        extra["twitch_id"] = str(twitch_id)

                    # Extract media
                    if avatar := payload.get("avatar"):
                        media["avatar"] = str(avatar).strip()
                    if banner := payload.get("cover_image_url"):
                        media["banner"] = str(banner).strip()

                    return Result.taken(extra=extra, media=media, url=show_url)
            except Exception:
                return Result.error("Failed to parse Faceit JSON response", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return impersonate_validate(url, process, headers=headers, show_url=show_url, impersonate="chrome")
