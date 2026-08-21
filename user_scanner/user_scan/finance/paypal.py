import html
import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_paypal(user: str) -> Result:
    """Validate a PayPal.Me username on PayPal (paypal.com)."""
    url = f"https://www.paypal.com/paypalme/{user}"
    show_url = f"https://www.paypal.com/paypalme/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # Extract OpenGraph title and description
        og_title_match = re.search(r'<meta property="og:title" content="(.*?)"', response.text, re.IGNORECASE)
        raw_og_title = og_title_match.group(1).strip() if og_title_match else ""
        og_title = html.unescape(raw_og_title)

        og_desc_match = re.search(r'<meta property="og:description" content="(.*?)"', response.text, re.IGNORECASE)
        raw_og_desc = og_desc_match.group(1).strip() if og_desc_match else ""
        og_desc = html.unescape(raw_og_desc)

        has_user_in_desc = f"paypal.me/{user.lower()}" in og_desc.lower()

        # 1. Explicit verification of available / not-found state
        # PayPal returns 404 OR 200 with generic "Get your very own PayPal.Me link" landing page
        if (
            response.status_code == 404
            or "we couldn't find this page" in response_text_lower
            or "we can't seem to find the page" in response_text_lower
            or "isn't active" in response_text_lower
            or og_title.lower() in ["get your very own paypal.me link", "paypal.me", "paypal", ""]
            or not has_user_in_desc
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + data extraction
        if response.status_code == 200 and has_user_in_desc:
            extra = {"handle": user}
            media = {}

            # Extract user's display name from "Pay <Name> using PayPal.Me"
            name_match = re.search(r"Pay\s+(.*?)\s+using\s+PayPal\.Me", og_title, re.IGNORECASE)
            if name_match:
                extra["name"] = name_match.group(1).strip()
            elif og_title and "paypal" not in og_title.lower():
                extra["name"] = og_title

            og_img_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text, re.IGNORECASE)
            if og_img_match:
                img_url = og_img_match.group(1).strip()
                if img_url and "pplogo" not in img_url.lower() and "paypal-logo" not in img_url.lower():
                    media["avatar"] = img_url

            return Result.taken(extra=extra, media=media, url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
