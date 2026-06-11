import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_mastodon(user: str) -> Result:
    if not (3 <= len(user) <= 30):
        return Result.error("Length must be 3-30 characters")

    if not re.match(r"^[a-zA-Z0-9_-]+$", user):
        return Result.error(
            "Usernames can only contain letters, numbers, underscores and hyphens"
        )

    if not re.match(r"^[a-zA-Z0-9].*[a-zA-Z0-9]$", user):
        return Result.error("Username must start and end with a letter or number")

    url = f"https://mastodon.social/api/v1/accounts/lookup?acct={user}"
    show_url = f"https://mastodon.social/@{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            extra = {}
            try:
                data = response.json()
                if data.get("id"):
                    extra["id"] = data.get("id")
                if data.get("display_name"):
                    extra["display_name"] = data.get("display_name")
                if data.get("note"):
                    import re as local_re
                    clean_note = local_re.sub('<[^<]+?>', '', data.get("note"))
                    extra["bio"] = clean_note.strip()
                if data.get("followers_count") is not None:
                    extra["followers"] = data.get("followers_count")
                if data.get("following_count") is not None:
                    extra["following"] = data.get("following_count")
                if data.get("statuses_count") is not None:
                    extra["posts"] = data.get("statuses_count")
                if data.get("avatar"):
                    extra["avatar"] = data.get("avatar")
            except Exception:
                pass
            return Result.taken(extra=extra)
        else:
            return Result.error(f"HTTP {response.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=True
    )

