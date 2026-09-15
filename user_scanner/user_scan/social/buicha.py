from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_buicha(user: str) -> Result:
    url = "https://buicha.social/api/users/show"
    show_url = f"https://buicha.social/@{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            try:
                data = response.json()
                err_code = data.get("error", {}).get("code")
                err_msg = str(data.get("error", {}).get("message", "")).lower()
                if err_code == "NO_SUCH_USER" or "no such user" in err_msg:
                    return Result.available(url=show_url)
            except Exception:
                pass
            return Result.error("Misskey 404 response missing expected error payload")

        if response.status_code == 200:
            try:
                data = response.json()
                if (
                    data.get("id")
                    and str(data.get("username", "")).lower() == user.lower()
                ):
                    extra: dict[str, str] = {}
                    media: dict[str, str] = {}

                    if data.get("name"):
                        extra["name"] = str(data["name"])
                    if data.get("description"):
                        extra["bio"] = str(data["description"]).strip()
                    if data.get("createdAt"):
                        extra["joined"] = str(data["createdAt"])
                    if data.get("followersCount") is not None:
                        extra["followers"] = str(data["followersCount"])
                    if data.get("followingCount") is not None:
                        extra["following"] = str(data["followingCount"])
                    if data.get("notesCount") is not None:
                        extra["posts"] = str(data["notesCount"])
                    if data.get("avatarUrl"):
                        media["avatar"] = str(data["avatarUrl"])

                    return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                pass
            return Result.error("Misskey 200 response missing valid user payload")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(
        url,
        process,
        headers=headers,
        json={"username": user},
        method="POST",
        show_url=show_url,
        follow_redirects=True,
    )
