import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_substack(user: str) -> Result:
    # Substack public profile API endpoint
    url = f"https://substack.com/api/v1/user/{user}/public_profile"
    show_url = f"https://substack.com/@{user}"

    def process(r):
        if r.status_code == 200:
            try:
                data = json.loads(r.text)
                # Claimed profile has an id and name
                if "id" in data:
                    extra = {}
                    if data.get("name"):
                        extra["display_name"] = data.get("name")
                    if data.get("handle"):
                        extra["handle"] = data.get("handle")
                    if data.get("bio"):
                        extra["bio"] = data.get("bio")
                    if data.get("photo_url"):
                        extra["avatar_url"] = data.get("photo_url")

                    # Extract publication info if they have one
                    primary_pub = data.get("primaryPublication") or {}
                    if primary_pub.get("name"):
                        extra["publication_name"] = primary_pub.get("name")
                    if primary_pub.get("subdomain"):
                        extra["publication_url"] = f"https://{primary_pub.get('subdomain')}.substack.com"

                    # Follower/subscriber counts
                    if data.get("subscriberCountNumber") is not None:
                        extra["subscribers"] = int(data.get("subscriberCountNumber"))
                    if data.get("followerCount") is not None:
                        extra["followers"] = int(data.get("followerCount"))

                    return Result.taken(extra=extra)
            except Exception:
                pass

        if r.status_code == 404:
            try:
                data = json.loads(r.text)
                if data.get("error") == "profile not found":
                    return Result.available()
            except Exception:
                pass
            return Result.available()

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=True
    )
