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

    def _clean_json_url(value: str) -> str:
        return re.sub(r"\\u002[fF]", "/", value).strip()

    def process(response):
        response_text_lower = response.text.lower()

        og_title_match = re.search(r'<meta property="og:title" content="(.*?)"', response.text, re.IGNORECASE)
        raw_og_title = og_title_match.group(1).strip() if og_title_match else ""
        og_title = html.unescape(raw_og_title)

        og_desc_match = re.search(r'<meta property="og:description" content="(.*?)"', response.text, re.IGNORECASE)
        raw_og_desc = og_desc_match.group(1).strip() if og_desc_match else ""
        og_desc = html.unescape(raw_og_desc)

        has_user_in_desc = f"paypal.me/{user.lower()}" in og_desc.lower()

        if (
            response.status_code == 404
            or "we couldn't find this page" in response_text_lower
            or "we can't seem to find the page" in response_text_lower
            or "isn't active" in response_text_lower
            or og_title.lower() in ["get your very own paypal.me link", "paypal.me", "paypal", ""]
            or not has_user_in_desc
        ):
            return Result.available(url=show_url)

        if response.status_code == 200 and has_user_in_desc:
            extra = {"handle": user}
            media = {}

            slug_match = re.search(
                r'"recipientSlugDetails":\s*\{(.{0,6000}?)"personalizationSettings"', response.text, re.DOTALL
            )
            if slug_match:
                blob = slug_match.group(1)

                name_match = re.search(r'"(?:displayName|alternateFullName)":"([^"]+)"', blob)
                if name_match:
                    extra["name"] = name_match.group(1)
                given_name = re.search(r'"givenName":"([^"]*)"', blob)
                if given_name and "name" not in extra:
                    given = given_name.group(1)
                    family = re.search(r'"familyName":"([^"]*)"', blob)
                    full = f"{given} {(family.group(1) if family else '')}".strip()
                    if full:
                        extra["name"] = full
                if match := re.search(r'"displayAddress":"([^"]+)"', blob):
                    extra["country"] = match.group(1)
                if match := re.search(r'"primaryCurrencyCode":"([^"]+)"', blob):
                    extra["currency"] = match.group(1)
                if match := re.search(r'"intent":"([^"]+)"', blob):
                    extra["account_type"] = match.group(1)
                for key, pattern in [
                    ("twitter", r'"twitterHandle":"([^"]+)"'),
                    ("instagram", r'"instagramUsername":"([^"]+)"'),
                    ("facebook", r'"facebookUrl":"([^"]+)"'),
                    ("website", r'"website":"([^"]+)"'),
                ]:
                    if match := re.search(pattern, blob):
                        value = _clean_json_url(match.group(1))
                        if value:
                            existing = extra.get("social")
                            extra["social"] = f"{existing} {value}" if existing else value

                if match := re.search(r'"profilePhotoUrl":"([^"]+)"', blob):
                    media["avatar"] = _clean_json_url(match.group(1))
                if match := re.search(r'"coverPhotoUrl":"([^"]+)"', response.text):
                    media["banner"] = _clean_json_url(match.group(1))

            if "avatar" not in media:
                og_img_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text, re.IGNORECASE)
                if og_img_match:
                    img_url = og_img_match.group(1).strip()
                    if img_url and "pplogo" not in img_url.lower() and "paypal-logo" not in img_url.lower():
                        media["avatar"] = img_url

            if "name" not in extra and "paypal" not in og_title.lower():
                name_match = re.search(r"Pay\s+(.*?)\s+using\s+PayPal\.Me", og_title, re.IGNORECASE)
                if name_match:
                    extra["name"] = name_match.group(1).strip()

            return Result.taken(extra=extra, media=media, url=show_url)

        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
