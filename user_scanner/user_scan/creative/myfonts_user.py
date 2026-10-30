import re
import urllib.parse

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_myfonts_user(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://www.myfonts.com/collections/{encoded_user}"
    show_url = f"https://www.myfonts.com/collections/{encoded_user}"

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code == 200:
            text = response.text
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
                "404 not found",
            ]
            if any(marker in text_lower for marker in not_found_markers):
                return Result.available(url=show_url)

            extra: dict[str, str] = {}
            media: dict[str, str] = {}

            # Extract title or heading if present
            title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
            if title_match:
                title_clean = title_match.group(1).strip()
                if title_clean and len(title_clean) < 120:
                    extra["title"] = title_clean

            # Extract description if present and not generic
            desc_match = re.search(
                r'<meta\s+(?:name|property)="og:description"\s+content="([^"]+)"',
                text,
                re.IGNORECASE,
            )
            if desc_match:
                desc_clean = desc_match.group(1).strip()
                if desc_clean and not desc_clean.startswith("Welcome to MyFonts"):
                    extra["description"] = desc_clean

            # Extract avatar / hero img if present
            avatar_match = re.search(
                r'<img[^>]+src=["\'](https?://[^"\']*(?:avatar|profile|user|foundry)[^"\']*)["\']',
                text,
                re.IGNORECASE,
            )
            if avatar_match:
                media["avatar"] = avatar_match.group(1)

            return Result.taken(url=show_url, extra=extra, media=media if media else None)

        return Result.error(f"Unexpected status code: {response.status_code}")

    return impersonate_validate(url, process, show_url=show_url, allow_redirects=True)

