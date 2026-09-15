import html
import json
import re
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

NOT_FOUND = "The page you requested was not found."
PAYHIP_DATA = re.compile(r"window\.payhipShop\s*=\s*(\{.*\});")


def validate_payhip(user: str) -> Result:
    url = f"https://payhip.com/{quote(user, safe='')}"

    def process(response) -> Result:
        if (
            response.status_code == 404
            and "<title>404 Page Not Found</title>" in response.text
            and NOT_FOUND in response.text
        ):
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected Payhip response: {response.status_code}")

        match = PAYHIP_DATA.search(response.text)
        if not match:
            return Result.error("Payhip profile data was missing")
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return Result.error("Invalid Payhip profile data")

        profile = data.get("user")
        if (
            not isinstance(profile, dict)
            or str(profile.get("username", "")).casefold() != user.casefold()
        ):
            return Result.error("Payhip profile did not match the requested username")

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
                "bio": " ".join(html.unescape(re.sub(r"<[^>]+>", " ", bio)).split()),
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

    return generic_validate(url, process, show_url=url, follow_redirects=True)
