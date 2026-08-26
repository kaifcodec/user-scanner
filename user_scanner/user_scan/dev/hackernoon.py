import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_hackernoon(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://us-central1-hackernoon-app.cloudfunctions.net/profilesApi/?handle={encoded_user}"
    show_url = f"https://hackernoon.com/u/{encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            try:
                data = response.json()
                if data.get("ok") is False or "profile" not in data:
                    return Result.available()
            except Exception:
                pass
            return Result.error("HackerNoon 404 response missing expected error structure")

        if response.status_code == 200:
            try:
                data = response.json()
                profile = data.get("profile")
                if profile and isinstance(profile, dict) and profile.get("handle"):
                    extra: dict[str, str] = {}
                    media: dict[str, str] = {}

                    if profile.get("displayName"):
                        extra["name"] = str(profile["displayName"])
                    if profile.get("bio"):
                        extra["bio"] = str(profile["bio"])
                    if profile.get("location"):
                        extra["location"] = str(profile["location"])
                    if profile.get("totalStories") is not None:
                        extra["stories"] = str(profile["totalStories"])
                    if profile.get("avatar"):
                        media["avatar"] = str(profile["avatar"])

                    social_media = profile.get("socialMedia")
                    if isinstance(social_media, dict):
                        for k, v in social_media.items():
                            if v:
                                extra[k] = str(v)

                    return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                pass
            return Result.error("HackerNoon 200 response missing valid profile payload")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
