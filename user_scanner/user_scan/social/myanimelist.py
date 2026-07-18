import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_myanimelist(user: str) -> Result:
    url = f"https://myanimelist.net/profile/{user}"
    show_url = f"https://myanimelist.net/profile/{user}"

    def process(r):
        if r.status_code == 404:
            return Result.available()

        if r.status_code == 200:
            extra = {}
            # Verify if user profile loaded
            if "has deleted their account" in r.text or "not found" in r.text.lower():
                return Result.available()

            # Extra info extraction from profile status list
            for key, field_name in [
                ("Last Online", "last_online"),
                ("Gender", "gender"),
                ("Birthday", "birthday"),
                ("Location", "location"),
                ("Joined", "joined"),
            ]:
                match = re.search(
                    rf'<span class="user-status-title[^"]*"[^>]*>{key}</span>[^<]*<span class="user-status-data[^"]*"[^>]*>([^<]+)</span>',
                    r.text,
                )
                if match:
                    extra[field_name] = match.group(1).strip()

            forum_match = re.search(
                r'<span class="user-status-title[^"]*"[^>]*>Forum Posts</span>[^<]*<span class="user-status-data[^"]*"[^>]*>([^<]+)</span>',
                r.text,
            )
            if forum_match:
                extra["forum_posts"] = forum_match.group(1).strip()

            return Result.taken(extra=extra)

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=True
    )
