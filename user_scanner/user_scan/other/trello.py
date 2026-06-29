from user_scanner.core.orchestrator import Result, generic_validate


def validate_trello(user):
    url = f"https://trello.com/1/Members/{user}"
    show_url = f"https://trello.com/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data and data.get("id"):
                    extras = {
                        "id": data.get("id"),
                        "fullName": data.get("fullName"),
                        "bio": data.get("bio"),
                        "initials": data.get("initials"),
                        "username": data.get("username"),
                    }

                    return Result.taken(extras=extras)
            except Exception:
                pass
        elif response.status_code == 404 or response.status_code == 401:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    return generic_validate(url, process, show_url=show_url, headers=headers)
