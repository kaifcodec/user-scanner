import json
import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_hackernoon(user: str) -> Result:
    url = f"https://hackernoon.com/u/{user}"
    show_url = f"https://hackernoon.com/u/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        if response.status_code == 200:
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', response.text)
            if not match:
                if f'"handle":"{user}"' in response.text or '"displayName":' in response.text:
                    return Result.taken(url=show_url)
                return Result.available()

            try:
                data = json.loads(match.group(1))
                profile = data.get("props", {}).get("pageProps", {}).get("data", {}).get("profile")

                if profile and profile.get("handle"):
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
                else:
                    return Result.available()
            except Exception:
                return Result.available()

        if response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
