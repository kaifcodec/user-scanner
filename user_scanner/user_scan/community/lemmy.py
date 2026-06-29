import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_lemmy(user: str) -> Result:
    """Check username availability on Lemmy (lemmy.world instance)"""

    # Lemmy username rules: 3-20 chars, alphanumeric and underscores only
    if not (3 <= len(user) <= 20):
        return Result.error("Length must be 3-20 characters")

    if not re.match(r"^[a-zA-Z0-9_]+$", user):
        return Result.error("Only letters, numbers, and underscores allowed")

    url = f"https://lemmy.world/api/v3/user?username={user}"
    show_url = f"https://lemmy.world/u/{user}"

    def process(response):
        if response.status_code in [400, 404]:
            return Result.available()
        if response.status_code == 200:
            extra = {}
            try:
                data = response.json()
                person_view = data.get("person_view", {})
                person = person_view.get("person", {})
                counts = person_view.get("counts", {})

                extra["id"] = person.get("id")
                extra["name"] = person.get("name")
                extra["display_name"] = person.get("display_name")
                extra["avatar"] = person.get("avatar")
                extra["joined"] = person.get("published")
                extra["bot"] = person.get("bot_account")
                extra["admin"] = person_view.get("is_admin")
                extra["posts"] = counts.get("post_count")
                extra["comments"] = counts.get("comment_count")

            except Exception:
                pass
            return Result.taken(extra=extra)
        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, timeout=5.0)
