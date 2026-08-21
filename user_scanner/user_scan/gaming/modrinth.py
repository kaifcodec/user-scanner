import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_modrinth(user: str) -> Result:
    """Validate a username on Modrinth (modrinth.com)."""
    url = f"https://api.modrinth.com/v2/user/{user}"
    show_url = f"https://modrinth.com/user/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    def process(response):
        # 1. Explicit check for not-found HTTP status
        if response.status_code == 404:
            return Result.available(url=show_url)

        # 2. Explicit verification of 200 OK + Modrinth user JSON response
        if response.status_code == 200 and "username" in response.text:
            try:
                data = json.loads(response.text)
                if (data.get("username") or "").lower() == user.lower() or data.get("id"):
                    extra = {}
                    media = {}

                    if username := data.get("username"):
                        extra["username"] = str(username).strip()
                    if name := data.get("name"):
                        extra["name"] = str(name).strip()
                    if user_id := data.get("id"):
                        extra["user_id"] = str(user_id).strip()
                    if role := data.get("role"):
                        extra["role"] = str(role).strip()
                    if bio := data.get("bio"):
                        extra["bio"] = str(bio).strip()
                    if created := data.get("created"):
                        extra["created"] = str(created).strip()

                    if avatar := data.get("avatar_url"):
                        media["avatar"] = str(avatar).strip()

                    return Result.taken(extra=extra, media=media, url=show_url)
            except Exception:
                return Result.error("Failed to parse Modrinth JSON response", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
