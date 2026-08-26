import urllib.parse
from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.orchestrator import Result

def validate_artstation(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://www.artstation.com/users/{encoded_user}.json"
    show_url = f"https://www.artstation.com/{encoded_user}"

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and (data.get("username") or data.get("full_name") or data.get("id")):
                    extra: dict[str, str] = {}
                    media: dict[str, str] = {}

                    if data.get("full_name"):
                        extra["name"] = str(data["full_name"])
                    if data.get("headline"):
                        extra["headline"] = str(data["headline"])
                    if data.get("city"):
                        extra["city"] = str(data["city"])
                    if data.get("country"):
                        extra["country"] = str(data["country"])
                    if data.get("followers_count") is not None:
                        extra["followers"] = str(data["followers_count"])
                    if data.get("large_avatar_url"):
                        media["avatar"] = str(data["large_avatar_url"])

                    return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                pass
            return Result.error("ArtStation 200 response missing valid user payload")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return impersonate_validate(
        url,
        process,
        warmup_url="https://www.artstation.com/",
        impersonate="chrome120",
        show_url=show_url,
    )
