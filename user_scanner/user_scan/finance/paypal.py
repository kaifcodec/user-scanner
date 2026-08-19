import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_paypal(user: str) -> Result:
    """Validate a PayPal.Me username on PayPal (paypal.com)."""
    url = f"https://www.paypal.com/paypalme/{user}"
    show_url = f"https://www.paypal.com/paypalme/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit verification of available / not-found state (HTTP 404 or inactive link markers)
        if (
            response.status_code == 404
            or "we couldn't find this page" in response_text_lower
            or "we can't seem to find the page" in response_text_lower
            or "isn't active" in response_text_lower
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + data extraction
        if response.status_code == 200 and ("paypal.me" in response_text_lower or "paypal" in response_text_lower):
            title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE)
            og_title_match = re.search(r'<meta property="og:title" content="(.*?)"', response.text, re.IGNORECASE)

            if (title_match and "paypal.me" in title_match.group(1).lower()) or og_title_match or "pp-button" in response_text_lower:
                extra = {"handle": user}
                media = {}

                if og_title_match:
                    extra["name"] = og_title_match.group(1).strip()

                og_img_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text, re.IGNORECASE)
                if og_img_match:
                    img_url = og_img_match.group(1).strip()
                    if img_url and "paypal-logo" not in img_url.lower():
                        media["avatar"] = img_url

                return Result.taken(extra=extra, media=media, url=show_url)

            return Result.error("Could not verify PayPal.Me page details", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
