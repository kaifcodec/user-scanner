import html
import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_devpost(user: str) -> Result:
    """Validate a developer portfolio on Devpost (devpost.com)."""
    url = f"https://devpost.com/{user}"
    show_url = f"https://devpost.com/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit verification of available / not-found state (HTTP 404 or missing portfolio marker)
        title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE)
        raw_title = title_match.group(1).strip() if title_match else ""
        page_title = html.unescape(raw_title)

        if (
            response.status_code == 404
            or (response.status_code == 200 and page_title.lower() == "devpost" and "portfolio" not in response_text_lower)
            or "page not found" in response_text_lower
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + data extraction
        if response.status_code == 200 and "devpost" in response_text_lower:
            if "software portfolio" in page_title.lower() or f"/{user.lower()}" in response_text_lower:
                extra = {"username": user}
                media = {}

                if "'s (" in page_title or "’s (" in page_title:
                    name_part = re.split(r"['’]s\s*\(", page_title)[0].strip()
                    if name_part:
                        extra["name"] = name_part

                og_img_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text, re.IGNORECASE)
                if og_img_match:
                    img_url = og_img_match.group(1).strip()
                    if img_url and "default-avatar" not in img_url.lower():
                        media["avatar"] = img_url

                return Result.taken(extra=extra, media=media, url=show_url)

            return Result.error("Could not verify portfolio details on Devpost", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
