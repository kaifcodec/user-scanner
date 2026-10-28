import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_genius(user: str) -> Result:
    url = f"https://genius.com/{user.lower()}"
    show_url = f"https://genius.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html",
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()
        if response.status_code == 200:
            text = response.text
            og_url = f'property="og:url" content="https://genius.com/{user.lower()}"'
            if og_url not in text or 'followers_count&quot;:' not in text:
                return Result.error("Unexpected response body, report it via GitHub issues")

            extra = {}
            media = {}
            if title := re.search(r'property="og:title" content="([^"]+)"', text):
                extra["username"] = title.group(1)
            if match := re.search(r'followers_count&quot;:(\d+)', text):
                extra["followers"] = match.group(1)
            if match := re.search(r'followed_users_count&quot;:(\d+)', text):
                extra["following"] = match.group(1)
            if match := re.search(r'&quot;iq&quot;:(\d+)', text):
                extra["iq"] = match.group(1)
            if match := re.search(r'https://images\.genius\.com/avatars/medium/[0-9a-f]{32}', text):
                media["avatar"] = match.group(0)
            banner = None
            for match in re.finditer(r'header_image_url&quot;:&quot;(https://[^&]+)&quot;', text):
                if "default_banner" not in match.group(1):
                    banner = match.group(1)
            if banner:
                media["banner"] = banner
            return Result.taken(extra=extra, media=media)

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
