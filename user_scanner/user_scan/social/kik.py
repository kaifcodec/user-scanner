import re
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

_DISPLAY_NAME_RE = re.compile(r'<h1 class="display-name">([^<]*)</h1>')
_AVATAR_RE = re.compile(r'<meta property="og:image"\s+content="([^"]*)"')


def validate_kik(user: str) -> Result:
    """
    Check account existence on Kik via its kik.me share page.

    Kik returns HTTP 200 for both existing and non-existing usernames, so the
    verdict relies on page markers: a real profile has a non-empty og:image
    pointing at profilepics.cf.kik.com, while a missing profile ships an empty
    og:image and a blank display name.
    """
    url = f"https://kik.me/{quote(user, safe='')}"
    show_url = url

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        text = response.text

        avatar_match = _AVATAR_RE.search(text)
        avatar = avatar_match.group(1) if avatar_match else None
        name_match = _DISPLAY_NAME_RE.search(text)
        fullname = name_match.group(1).strip() if name_match else None

        # Taken state: Kik serves the profile picture CDN URL only for
        # accounts that actually exist.
        if (avatar and "profilepics.cf.kik.com" in avatar) or fullname:
            extra = {"fullname": fullname} if fullname else {}
            media = {"avatar": avatar} if avatar else {}
            return Result.taken(extra=extra, media=media)

        # Available state: both the avatar slot and the display name are
        # blank — verified against a nonexistent handle.
        if not avatar and not fullname:
            return Result.available(url=show_url)

        return Result.error("Ambiguous kik.me page: profile markers disagree")

    return generic_validate(url, process, show_url=show_url)
