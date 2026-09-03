import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_rhasspy(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://community.rhasspy.org/u/{encoded_user}.json"
    show_url = f"https://community.rhasspy.org/u/{encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            try:
                data = response.json()
                if (
                    data.get("error_type") == "not_found"
                    or any("not be found" in str(err).lower() for err in data.get("errors", []))
                ):
                    return Result.available(url=show_url)
            except Exception:
                pass
            return Result.error("Discourse 404 response missing expected error payload")

        if response.status_code == 200:
            try:
                data = response.json()
                user_obj = data.get("user")
                if user_obj and isinstance(user_obj, dict) and user_obj.get("username"):
                    extra: dict[str, str] = {}
                    media: dict[str, str] = {}

                    if user_obj.get("name"):
                        extra["name"] = str(user_obj["name"])
                    if user_obj.get("title"):
                        extra["title"] = str(user_obj["title"])
                    if user_obj.get("location"):
                        extra["location"] = str(user_obj["location"])
                    if user_obj.get("website_name") or user_obj.get("website"):
                        extra["website"] = str(user_obj.get("website") or user_obj.get("website_name"))
                    if user_obj.get("trust_level") is not None:
                        extra["trust_level"] = str(user_obj["trust_level"])
                    if user_obj.get("badge_count") is not None:
                        extra["badges"] = str(user_obj["badge_count"])
                    if user_obj.get("created_at"):
                        extra["joined"] = str(user_obj["created_at"])
                    if user_obj.get("bio_raw") or user_obj.get("bio_cooked"):
                        extra["bio"] = str(user_obj.get("bio_raw") or user_obj.get("bio_cooked"))

                    avatar_template = user_obj.get("avatar_template")
                    if avatar_template:
                        avatar_url = avatar_template.replace("{size}", "240")
                        if avatar_url.startswith("/"):
                            avatar_url = f"https://community.rhasspy.org{avatar_url}"
                        media["avatar"] = avatar_url

                    return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                pass
            return Result.error("Discourse 200 response missing valid user payload")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
