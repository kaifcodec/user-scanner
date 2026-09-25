import urllib.parse

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_git_selfprivacy_org(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://git.selfprivacy.org/api/v1/users/{encoded_user}"
    show_url = f"https://git.selfprivacy.org/{encoded_user}"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            try:
                data = response.json()
                msg = str(data.get("message", "")).lower()
                if "does not exist" in msg or "not found" in msg:
                    return Result.available(url=show_url)
            except Exception:
                pass
            return Result.error("Gitea 404 response missing expected error payload")

        if response.status_code == 200:
            try:
                data = response.json()
                if (data.get("username") or data.get("login")) and isinstance(data, dict):
                    extra: dict[str, str] = {}
                    media: dict[str, str] = {}

                    if data.get("full_name"):
                        extra["name"] = str(data["full_name"])
                    if data.get("location"):
                        extra["location"] = str(data["location"])
                    if data.get("website"):
                        extra["website"] = str(data["website"])
                    if data.get("description"):
                        extra["bio"] = str(data["description"])
                    if data.get("created"):
                        extra["joined"] = str(data["created"])
                    if data.get("avatar_url"):
                        media["avatar"] = str(data["avatar_url"])

                    return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                pass
            return Result.error("Gitea 200 response missing valid user payload")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=show_url,
        follow_redirects=True,
    )
