import re
import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_myvideogamelist_com(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://myvideogamelist.com/profile/{encoded_user}"
    show_url = f"https://myvideogamelist.com/profile/{encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code == 200:
            text = response.text
            user_lower = user.lower()
            text_lower = text.lower()

            # Check for soft 404 or not-found text
            not_found_markers = [
                "user not found",
                "member not found",
                "profile does not exist",
                "user does not exist",
                "page not found",
                "no user found",
                "could not be found",
            ]
            if any(marker in text_lower for marker in not_found_markers):
                return Result.available(url=show_url)

            # Strict verification of user presence in 200 response
            if user_lower in text_lower:
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                # Extract title or heading if present
                title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
                if title_match:
                    title_clean = title_match.group(1).strip()
                    if title_clean and len(title_clean) < 120:
                        extra["title"] = title_clean

                # Extract avatar img if present
                avatar_match = re.search(
                    r'<img[^>]+src=["\'](https?://[^"\']*(?:avatar|profile|user)[^"\']*)["\']',
                    text,
                    re.IGNORECASE,
                )
                if avatar_match:
                    media["avatar"] = avatar_match.group(1)

                return Result.taken(url=show_url, extra=extra, media=media)

            return Result.error("Profile page returned 200 but target username was not found")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
