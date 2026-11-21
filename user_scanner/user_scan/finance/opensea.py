import html
import re
import urllib.parse

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_opensea(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://opensea.io/{encoded_user}"
    show_url = f"https://opensea.io/{encoded_user}"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        status = response.status_code

        if status in (404, 410):
            return Result.available(url=show_url)

        if status == 200:
            text = response.text
            title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ""

            if "- Profile | OpenSea" in title:
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                desc_match = re.search(
                    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
                    text,
                    re.IGNORECASE,
                )
                if desc_match:
                    bio = html.unescape(desc_match.group(1).strip())
                    if bio and "exchange everything" not in bio.lower():
                        extra["bio"] = bio

                img_match = re.search(
                    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']',
                    text,
                    re.IGNORECASE,
                )
                if img_match:
                    media["avatar"] = img_match.group(1).strip()

                return Result.taken(url=show_url, extra=extra, media=media)

            if "exchange everything" in title.lower() or "marketplace" in title.lower():
                return Result.available(url=show_url)

            return Result.available(url=show_url)

        return Result.error(f"Unexpected response status {status}")

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=show_url,
        follow_redirects=True,
    )
