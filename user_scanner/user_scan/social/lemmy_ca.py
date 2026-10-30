import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_lemmy_ca(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = "https://lemmy.ca/api/v3/user"
    show_url = f"https://lemmy.ca/u/{encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response) -> Result:
        if response.status_code in (400, 404):
            try:
                data = response.json()
                err = str(data.get("error", "")).lower()
                if "couldnt_find" in err or "not_found" in err:
                    return Result.available(url=show_url)
            except Exception:
                pass
            return Result.error(f"Lemmy {response.status_code} response missing expected error payload")

        if response.status_code == 200:
            try:
                data = response.json()
                person_view = data.get("person_view", {})
                person = person_view.get("person", {})
                if person and person.get("name") and str(person.get("name")).lower() == user.lower():
                    extra: dict[str, str | int | bool] = {}
                    media: dict[str, str] = {}

                    if person.get("display_name"):
                        extra["display_name"] = str(person["display_name"])
                    if person.get("bio"):
                        extra["bio"] = str(person["bio"])
                    if person.get("published"):
                        extra["joined"] = str(person["published"])
                    if person.get("matrix_user_id"):
                        extra["matrix"] = str(person["matrix_user_id"])
                    if person.get("actor_id"):
                        extra["actor_id"] = str(person["actor_id"])
                    if person.get("bot_account") is not None:
                        extra["bot_account"] = bool(person["bot_account"])
                    if person.get("banned") is not None:
                        extra["banned"] = bool(person["banned"])

                    counts = person_view.get("counts", {})
                    if counts.get("post_count") is not None:
                        extra["post_count"] = int(counts["post_count"])
                    if counts.get("comment_count") is not None:
                        extra["comment_count"] = int(counts["comment_count"])
                    if person_view.get("is_admin") is not None:
                        extra["is_admin"] = bool(person_view["is_admin"])

                    avatar = person.get("avatar")
                    if avatar and isinstance(avatar, str) and avatar.startswith("http"):
                        media["avatar"] = avatar

                    return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                pass
            return Result.error("Lemmy 200 response missing valid person payload")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(
        url,
        process,
        headers=headers,
        params={"username": user},
        show_url=show_url,
        follow_redirects=True,
    )
