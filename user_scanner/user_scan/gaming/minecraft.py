from user_scanner.core.orchestrator import generic_validate, Result
from user_scanner.core.helpers import get_random_user_agent

def validate_minecraft(user):
    url = f"https://api.mojang.com/minecraft/profile/lookup/name/{user}"
    show_url = f"https://namemc.com/profile/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json"
    }

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                extra = {}
                if uuid := data.get("id"): extra["uuid"] = uuid
                if name := data.get("name"): extra["username"] = name
                return Result.taken(extra=extra)
            except Exception:
                pass
            return Result.error("200 response status with no recognizable data, report it via GitHub issues")
        elif response.status_code == 204 or response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url)
