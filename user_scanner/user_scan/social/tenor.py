import html
import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_tenor(user: str) -> Result:
    """Validate a creator profile on Tenor (tenor.com)."""
    url = f"https://tenor.com/users/{user}"
    show_url = f"https://tenor.com/users/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE)
        raw_title = title_match.group(1).strip() if title_match else ""
        title = html.unescape(raw_title)
        norm_title = title.replace("’", "'").lower()

        # 1. Explicit verification of available / not-found state
        if (
            response.status_code == 404
            or "404 error" in norm_title
            or "page not found" in response.text.lower()
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + data extraction
        if (
            response.status_code == 200
            and "tenor" in norm_title
            and (f"{user.lower()}'s gifs" in norm_title or f"{user.lower()}'s" in norm_title)
        ):
            extra = {"username": user}
            media = {}

            # Extract avatar or featured gif from OpenGraph
            img_match = re.search(r'<meta content="(.*?)" property="og:image"', response.text, re.IGNORECASE)
            if not img_match:
                img_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text, re.IGNORECASE)
            if img_match:
                img_url = img_match.group(1).strip()
                if img_url and "tenor-logo" not in img_url.lower():
                    media["avatar"] = img_url

            return Result.taken(extra=extra, media=media, url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
