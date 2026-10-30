import urllib.parse

from user_scanner.core.orchestrator import Result, generic_validate


def validate_lemmy_rochegmr_com(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = "https://lemmy.rochegmr.com/api/v3/user"
    show_url = f"https://lemmy.rochegmr.com/u/{encoded_user}"

    headers = {
        "User-Agent": "user-scanner/1.0",
        "Accept": "application/json",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            try:
                data = response.json()
                err = str(data.get("error", "")).lower()
                if "couldnt_find" in err or "not_found" in err:
                    return Result.available(url=show_url)
            except Exception:
                pass
            return Result.error("Lemmy 404 response missing expected error payload")

        if response.status_code == 200:
            try:
                data = response.json()
                pv = data.get("person_view", {})
                person = pv.get("person", {})
                counts = pv.get("counts", {})
                if person and person.get("name") and str(person.get("name")).lower() == user.lower():
                    extra: dict[str, str] = {}
                    media: dict[str, str] = {}

                    if person.get("id"):
                        extra["id"] = str(person["id"])
                    if person.get("display_name"):
                        extra["display_name"] = str(person["display_name"])
                    if person.get("bio"):
                        extra["bio"] = str(person["bio"])
                    if person.get("published"):
                        extra["joined"] = str(person["published"])
                    if counts.get("post_count") is not None:
                        extra["post_count"] = str(counts["post_count"])
                    if counts.get("comment_count") is not None:
                        extra["comment_count"] = str(counts["comment_count"])
                    if pv.get("is_admin") is not None:
                        extra["is_admin"] = str(pv["is_admin"])
                    if person.get("matrix_user_id"):
                        extra["matrix"] = str(person["matrix_user_id"])
                    if person.get("actor_id"):
                        extra["actor_id"] = str(person["actor_id"])

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
