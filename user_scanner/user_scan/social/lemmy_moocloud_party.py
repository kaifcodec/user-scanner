import urllib.parse

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_lemmy_moocloud_party(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = "https://lemmy.moocloud.party/api/v3/user"
    show_url = f"https://lemmy.moocloud.party/u/{encoded_user}"
    headers = {
        "User-Agent": get_random_user_agent(),
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
                person_view = data.get("person_view", {})
                person = person_view.get("person", {})
                if person and person.get("name"):
                    extra: dict[str, str] = {}
                    media: dict[str, str] = {}

                    if person.get("display_name"):
                        extra["display_name"] = str(person["display_name"])
                    if person.get("bio"):
                        extra["bio"] = str(person["bio"])
                    if person.get("matrix_user_id"):
                        extra["matrix"] = str(person["matrix_user_id"])
                    if person.get("bot") is not None:
                        extra["is_bot"] = str(person["bot"])
                    if person_view.get("counts"):
                        counts = person_view["counts"]
                        if counts.get("post_count") is not None:
                            extra["posts"] = str(counts["post_count"])
                        if counts.get("comment_count") is not None:
                            extra["comments"] = str(counts["comment_count"])

                    if person.get("avatar"):
                        media["avatar"] = str(person["avatar"])
                    if person.get("banner"):
                        media["banner"] = str(person["banner"])

                    return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                pass
            return Result.error("Lemmy 200 response missing valid person payload")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(
        url,
        process,
        params={"username": user},
        headers=headers,
        show_url=show_url,
        follow_redirects=True,
    )
