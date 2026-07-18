import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_speakerdeck(user: str) -> Result:
    url = f"https://speakerdeck.com/{user}"
    show_url = f"https://speakerdeck.com/{user}"

    def process(r):
        if r.status_code == 404:
            return Result.available()

        if r.status_code == 200:
            if "User Not Found" in r.text:
                return Result.available()

            extra = {}
            # Extract display name
            name_match = re.search(r"<h1>\s*([^\n<]+)\s*</h1>", r.text)
            if name_match:
                extra["display_name"] = name_match.group(1).strip()

            # Extract avatar URL
            avatar_match = re.search(r'<img[^>]+class="[^"]*avatar[^"]*"[^>]+src="([^"]+)"', r.text)
            if avatar_match:
                extra["avatar_url"] = avatar_match.group(1).strip()

            # Extract decks count
            decks_match = re.search(r"([0-9]+)\s*Decks", r.text)
            if decks_match:
                extra["decks"] = int(decks_match.group(1))

            # Extract following count
            following_match = re.search(r"([0-9]+)\s*Following", r.text)
            if following_match:
                extra["following"] = int(following_match.group(1))

            # Extract followers count
            followers_match = re.search(r"([0-9]+)\s*Followers", r.text)
            if followers_match:
                extra["followers"] = int(followers_match.group(1))

            return Result.taken(extra=extra)

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=True
    )
