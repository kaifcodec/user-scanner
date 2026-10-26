import html
import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_flipsnack(user: str) -> Result:
    url = f"https://www.flipsnack.com/{user}/"

    def process(response):
        if response.status_code == 404:
            if "This page does not exist" in response.text:
                return Result.available()
            return Result.error("Unrecognized Flipsnack not-found response")

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        title = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.S)
        if not title:
            return Result.error("Flipsnack profile markers were missing")

        page_title = html.unescape(title.group(1)).strip()

        display = re.search(
            r"(.*),\s*" + re.escape(user) + r"\s*-\s*Flipsnack\s*$",
            page_title,
            re.IGNORECASE,
        )
        if not display:
            return Result.error("Flipsnack profile marker did not match target")

        extra = {}
        media = {}
        name = display.group(1).strip()
        if name and name.lower() != user.lower():
            extra["fullname"] = name

        count = re.search(r"has (\d+) public flipbooks?\b", response.text)
        if count:
            extra["flipbooks"] = count.group(1)

        avatar = re.search(
            r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"',
            response.text,
        )
        if avatar:
            media["avatar"] = html.unescape(avatar.group(1)).strip()

        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=url, follow_redirects=True)
