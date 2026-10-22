from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_w3schools(user: str) -> Result:
    url = f"https://pathfinder-api.kai.w3spaces.com/public-profile-api/{user}"
    show_url = f"https://my-learning.w3schools.com/user/{user}"
    headers = {"User-Agent": get_random_user_agent(), "Accept": "application/json"}

    def process(response) -> Result:
        if response.status_code == 200:
            extra = {}
            try:
                data = response.json()
                if "displayName" in data:
                    extra["name"] = data["displayName"]
                if "bio" in data and data["bio"]:
                    extra["bio"] = data["bio"]
                if "avatar" in data and data["avatar"]:
                    extra["avatar"] = data["avatar"]
            except Exception:
                pass
            return Result.taken(extra=extra if extra else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return generic_validate(url, process, show_url=show_url, headers=headers)
