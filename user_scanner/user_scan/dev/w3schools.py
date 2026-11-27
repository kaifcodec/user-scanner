from urllib.parse import quote
from user_scanner.core.orchestrator import Result, generic_validate


def validate_w3schools(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://pathfinder-api.kai.w3spaces.com/public-profile-api/{safe_user}"
    show_url = f"https://my-learning.w3schools.com/user/{user}"
    headers = {"Accept": "application/json"}

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, object] = {}
            media = {}
            try:
                data = response.json()
                if "displayName" in data and data["displayName"]:
                    extra["name"] = data["displayName"]
                if "bio" in data and data["bio"]:
                    extra["bio"] = data["bio"]
                if "avatar" in data and data["avatar"]:
                    media["avatar"] = data["avatar"]
            except Exception:
                pass
            return Result.taken(extra=extra if extra else None, media=media if media else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return generic_validate(url, process, show_url=show_url, headers=headers)
