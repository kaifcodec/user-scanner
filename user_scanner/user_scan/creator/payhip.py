import html
import json
import re
from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

NOT_FOUND = "The page you requested was not found."
PAYHIP_DATA = re.compile(r"window\.payhipShop\s*=\s*(\{.*\});")


def validate_payhip(user: str) -> Result:
    url = f"https://payhip.com/{quote(user, safe='')}"

    def process(response) -> Result:
        text = response.text
        if (
            response.status_code == 404
            and ("<title>404 Page Not Found</title>" in text or NOT_FOUND in text)
        ):
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected Payhip response: {response.status_code}")

        # Check for legacy JSON payload
        match = PAYHIP_DATA.search(text)
        if match:
            try:
                data = json.loads(match.group(1))
                profile = data.get("user")
                if (
                    isinstance(profile, dict)
                    and str(profile.get("username", "")).casefold() == user.casefold()
                ):
                    raw_bio = profile.get("bio")
                    bio = raw_bio if isinstance(raw_bio, str) else ""
                    bio_links = list(
                        dict.fromkeys(map(html.unescape, re.findall(r'href="([^"]+)"', bio)))
                    ) or None
                    social = profile.get("socialMedia")
                    social_links = (
                        {
                            key.removesuffix("Url").lower(): value
                            for key, value in social.items()
                            if key.endswith("Url") and isinstance(value, str)
                        }
                        if isinstance(social, dict)
                        else {}
                    )
                    not_required = profile.get("buyerAccountRequirementStatusIsNotRequired")
                    optional = profile.get("buyerAccountRequirementStatusIsOptional")
                    if not_required is True:
                        buyer_account_policy = "not_required"
                    elif optional is True:
                        buyer_account_policy = "optional"
                    elif not_required is False and optional is False:
                        buyer_account_policy = "required"
                    else:
                        buyer_account_policy = None

                    logo = (profile.get("resizedLogo") or {}).get("original") or {}
                    return Result.taken(
                        extra={
                            "uid": profile.get("userIdEncrypted"),
                            "name": profile.get("shopName"),
                            "bio": " ".join(html.unescape(re.sub(r"<[^>]+>", " ", bio)).split()) or None,
                            "bio_links": bio_links,
                            "currency": profile.get("currency"),
                            "website": profile.get("websiteUrl"),
                            "store_language": profile.get("shopLanguage"),
                            "custom_domain_name": profile.get("customDomainName"),
                            "paypal_enabled": profile.get("hasConnectedPaymentProviderPayPal"),
                            "stripe_enabled": profile.get("hasConnectedPaymentProviderStripe"),
                            "custom_domain_enabled": profile.get("customDomainEnabled"),
                            "reviews_enabled": profile.get("customerReviewsEnabled"),
                            "shipping_enabled": profile.get("shippingv2Enabled"),
                            "buyer_account_policy": buyer_account_policy,
                            "multiple_products": profile.get("hasMoreThanOneProduct"),
                            **social_links,
                        },
                        media={"avatar": logo.get("src")},
                    )
            except json.JSONDecodeError:
                pass

        # Modern Payhip store HTML payload
        author_m = re.search(r"var glob_author_username = '([^']+)';", text) or re.search(
            r'<meta property="username" value="([^"]+)"', text
        )
        if author_m and author_m.group(1).casefold() == user.casefold():
            extra: dict[str, str | bool | int | None] = {}
            media: dict[str, str] = {}

            title_m = re.search(r'<meta property="og:title" content="([^"]+)"', text) or re.search(
                r"<title>(.*?)</title>", text
            )
            if title_m:
                name_clean = html.unescape(title_m.group(1).removesuffix(" - Payhip").strip())
                if name_clean and name_clean.lower() != "login":
                    extra["name"] = name_clean

            desc_m = re.search(r'<meta property="og:description" content="([^"]+)"', text)
            if desc_m and desc_m.group(1).strip():
                extra["bio"] = html.unescape(desc_m.group(1).strip())

            curr_m = re.search(r"var glob_currency = '([^']+)';", text)
            if curr_m:
                extra["currency"] = html.unescape(curr_m.group(1).strip())

            img_m = re.search(r'<meta property="og:image" content="([^"]+)"', text)
            if img_m and img_m.group(1).strip():
                media["avatar"] = img_m.group(1).strip()

            return Result.taken(extra=extra, media=media)

        return Result.error("Payhip profile data was missing or mismatched")

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)
