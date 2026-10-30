import json
import re
from datetime import datetime, timezone

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_behance(user: str) -> Result:
    url = f"https://www.behance.net/{user}"
    show_url = f"https://www.behance.net/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, object] = {}
            media: dict[str, str] = {}
            match = re.search(
                r'<script type="application/json" id="beconfig-store_state">({.+?})</script>',
                response.text,
            )
            if match:
                try:
                    data = json.loads(match.group(1))
                    user_data = data.get("profile", {}).get("user", {})
                    if not user_data and "user" in data.get("profile", {}):
                        user_data = data["profile"]["user"]

                    if user_data.get("id"):
                        extra["id"] = str(user_data["id"])
                    if user_data.get("displayName"):
                        extra["fullname"] = user_data["displayName"]
                    if user_data.get("location"):
                        extra["location"] = user_data["location"]
                    if user_data.get("company"):
                        extra["company"] = user_data["company"]
                    if user_data.get("occupation"):
                        extra["occupation"] = user_data["occupation"]
                    if user_data.get("website"):
                        extra["website"] = user_data["website"]
                    if user_data.get("createdOn"):
                        extra["joined"] = datetime.fromtimestamp(
                            user_data["createdOn"], timezone.utc
                        ).strftime("%Y-%m-%d")

                    stats = user_data.get("stats", {})
                    if "followers" in stats:
                        extra["follower_count"] = stats["followers"]
                    if "following" in stats:
                        extra["following_count"] = stats["following"]
                    if "views" in stats:
                        extra["views_count"] = stats["views"]
                    if "appreciations" in stats:
                        extra["appreciations_count"] = stats["appreciations"]

                    # Extract avatar
                    images = user_data.get("images", {})
                    if isinstance(images, dict):
                        avatar = images.get("276") or images.get("138") or images.get("115")
                        if not avatar and isinstance(images.get("allAvailable"), list):
                            avail = images["allAvailable"]
                            if avail and isinstance(avail[-1], dict) and avail[-1].get("url"):
                                avatar = avail[-1]["url"]
                        if avatar and "default" not in avatar:
                            media["avatar"] = avatar
                except Exception:
                    pass

            return Result.taken(url=show_url, extra=extra, media=media if media else None)

        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return impersonate_validate(url, process, show_url=show_url, allow_redirects=True)

