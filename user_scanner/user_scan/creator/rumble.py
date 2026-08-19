import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_rumble(user: str) -> Result:
    """Validate a channel/creator on Rumble (rumble.com)."""
    url = f"https://rumble.com/c/{user}"
    show_url = f"https://rumble.com/c/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit verification of available / not-found state (HTTP 404 or 404 title)
        title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE)
        page_title = title_match.group(1).strip() if title_match else ""

        if (
            response.status_code == 404
            or "404 not found" in page_title.lower()
            or "page not found" in response_text_lower
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + data extraction
        if response.status_code == 200 and "rumble" in response_text_lower:
            if page_title and "404" not in page_title:
                extra = {"channel": user}
                media = {}

                channel_name = page_title.replace(" - Rumble", "").replace(" on Rumble", "").strip()
                if channel_name and channel_name.lower() != "rumble":
                    extra["name"] = channel_name

                og_img_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text, re.IGNORECASE)
                if og_img_match:
                    img_url = og_img_match.group(1).strip()
                    if img_url and "rumble-logo" not in img_url.lower():
                        media["avatar"] = img_url

                return Result.taken(extra=extra, media=media, url=show_url)

            return Result.error("Could not verify channel details on Rumble", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
