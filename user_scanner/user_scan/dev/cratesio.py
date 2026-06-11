from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate, Result


def validate_cratesio(user):
    url = f"https://crates.io/api/v1/users/{user}"
    show_url = f"https://crates.io/users/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
        "Referer": "https://crates.io/",
        "sec-fetch-mode": "cors",
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            extra = {}
            try:
                data = response.json()
                u_data = data.get("user", {})
                if u_data:
                    if u_data.get("id"):
                        extra["id"] = u_data.get("id")
                    if u_data.get("name"):
                        extra["name"] = u_data.get("name").strip()
                    if u_data.get("avatar"):
                        extra["avatar"] = u_data.get("avatar")
                    if u_data.get("url"):
                        extra["github_url"] = u_data.get("url")
            except Exception:
                pass
            return Result.taken(extra=extra)
        else:
            return Result.error(f"HTTP {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)

