from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_gitlab(user):
    url = f"https://gitlab.com/api/v4/users?username={user}"
    show_url = f"https://gitlab.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json, text/plain, */*",
    }

    def process(response):
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                if len(data) == 0:
                    return Result.available()
                else:
                    extra = {}
                    try:
                        u_data = data[0]
                        if u_data.get("id"):
                            extra["id"] = u_data.get("id")
                        if u_data.get("name"):
                            extra["name"] = u_data.get("name").strip()
                        if u_data.get("state"):
                            extra["state"] = u_data.get("state")
                        if u_data.get("avatar_url"):
                            extra["avatar"] = u_data.get("avatar_url")
                    except Exception:
                        pass
                    return Result.taken(extra=extra)
        return Result.error(f"Unexpected status or response: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)

