from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate, Result


def validate_dockerhub(user):
    url = f"https://hub.docker.com/v2/users/{user}/"
    show_url = f"https://hub.docker.com/u/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            extra = {}
            try:
                data = response.json()
                if data.get("id"):
                    extra["id"] = data.get("id")
                if data.get("full_name"):
                    extra["name"] = data.get("full_name").strip()
                if data.get("company"):
                    extra["company"] = data.get("company").strip()
                if data.get("location"):
                    extra["location"] = data.get("location").strip()
                if data.get("date_joined"):
                    extra["joined"] = data.get("date_joined")
                if data.get("type"):
                    extra["type"] = data.get("type")
            except Exception:
                pass
            return Result.taken(extra=extra)
        else:
            return Result.error(f"HTTP {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)

