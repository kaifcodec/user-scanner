import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_solo_to(user: str) -> Result:
    """Validate a creator profile on Solo.to (solo.to)."""
    url = f"https://solo.to/{user}"
    show_url = f"https://solo.to/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit verification of available / not-found state (HTTP 404 or Not Found title)
        title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE)
        page_title = title_match.group(1).strip() if title_match else ""

        if (
            response.status_code == 404
            or "not found · solo.to" in page_title.lower()
            or "page not found" in response_text_lower
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + data extraction
        if response.status_code == 200 and "solo.to" in response_text_lower:
            if "· solo.to" in page_title:
                extra = {"username": user}
                media = {}

                display_name = page_title.replace(" · solo.to", "").replace(" | solo.to", "").strip()
                if display_name and display_name.lower() != "not found":
                    extra["name"] = display_name

                og_img_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text, re.IGNORECASE)
                if og_img_match:
                    img_url = og_img_match.group(1).strip()
                    if img_url and "solo-logo" not in img_url.lower():
                        media["avatar"] = img_url

                return Result.taken(extra=extra, media=media, url=show_url)

            return Result.error("Could not verify profile details on Solo.to", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
