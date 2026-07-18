import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_boosty(user: str) -> Result:
    # Boosty API endpoint for user blog profile
    url = f"https://api.boosty.to/v1/blog/{user}"
    show_url = f"https://boosty.to/{user}"

    def process(r):
        if r.status_code == 200:
            try:
                data = json.loads(r.text)
                # If it's a valid blog, it contains a unique ID or title
                if "title" in data:
                    extra = {}
                    if data.get("title"):
                        extra["display_name"] = data.get("title")

                    counts = data.get("count", {})
                    if counts.get("subscribers") is not None:
                        extra["subscribers"] = int(counts.get("subscribers"))
                    if counts.get("posts") is not None:
                        extra["posts"] = int(counts.get("posts"))

                    owner = data.get("owner", {})
                    if owner.get("avatarUrl"):
                        extra["avatar_url"] = owner.get("avatarUrl")
                    if owner.get("name") and owner.get("name") != data.get("title"):
                        extra["owner_name"] = owner.get("name")

                    # Extract social links if present
                    links = []
                    for link in data.get("socialLinks", []):
                        if link.get("url"):
                            links.append(link.get("url"))
                    if links:
                        extra["links"] = links

                    return Result.taken(extra=extra)
            except Exception:
                pass

        if r.status_code == 404:
            try:
                data = json.loads(r.text)
                if data.get("error") == "blog_not_found":
                    return Result.available()
            except Exception:
                pass
            return Result.available()

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=True
    )
