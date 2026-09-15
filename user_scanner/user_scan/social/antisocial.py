import re
import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_antisocial(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://a.nti.social/api/v1/accounts/lookup?acct={encoded_user}"
    show_url = f"https://a.nti.social/users/{encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            try:
                data = response.json()
                err_msg = str(data.get("error", "")).lower()
                if "find user" in err_msg or "not found" in err_msg:
                    return Result.available(url=show_url)
            except Exception:
                pass
            return Result.error("Pleroma 404 response missing expected error payload")

        if response.status_code == 200:
            try:
                data = response.json()
                if (
                    data.get("id")
                    and str(data.get("username", "")).lower() == user.lower()
                ):
                    extra: dict[str, str] = {}
                    media: dict[str, str] = {}

                    if data.get("display_name"):
                        extra["name"] = str(data["display_name"])
                    if data.get("note"):
                        extra["bio"] = re.sub(r"<[^<]+?>", "", data["note"]).strip()
                    if data.get("created_at"):
                        extra["joined"] = str(data["created_at"])
                    if data.get("followers_count") is not None:
                        extra["followers"] = str(data["followers_count"])
                    if data.get("following_count") is not None:
                        extra["following"] = str(data["following_count"])
                    if data.get("statuses_count") is not None:
                        extra["posts"] = str(data["statuses_count"])
                    if data.get("avatar"):
                        media["avatar"] = str(data["avatar"])

                    return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                pass
            return Result.error("Pleroma 200 response missing valid account payload")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
