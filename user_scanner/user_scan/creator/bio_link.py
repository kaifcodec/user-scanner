import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_bio_link(user: str) -> Result:
    """Validate a creator profile on Bio.link (bio.link)."""
    url = f"https://bio.link/{user}"
    show_url = f"https://bio.link/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit verification of available / not-found state (HTTP 404 or 404 page title)
        title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE)
        page_title = title_match.group(1).strip() if title_match else ""

        if (
            response.status_code == 404
            or "page not found" in page_title.lower()
            or "page not found" in response_text_lower
            or "404" in page_title
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + data extraction
        if response.status_code == 200:
            extra = {"username": user}
            media = {}

            if page_title and "page not found" not in page_title.lower():
                display_name = page_title.replace(" - Bio.link", "").replace(" | Bio.link", "").strip()
                if display_name and display_name.lower() != "bio.link":
                    extra["name"] = display_name

            og_title_match = re.search(r'<meta property="og:title" content="(.*?)"', response.text, re.IGNORECASE)
            if og_title_match and "name" not in extra:
                og_name = og_title_match.group(1).strip()
                if og_name and og_name.lower() != "bio.link":
                    extra["name"] = og_name

            og_img_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text, re.IGNORECASE)
            if og_img_match:
                img_url = og_img_match.group(1).strip()
                if img_url and "bio-link-logo" not in img_url.lower():
                    media["avatar"] = img_url

            return Result.taken(extra=extra, media=media, url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
