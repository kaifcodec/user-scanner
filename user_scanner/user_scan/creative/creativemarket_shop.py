import json
import re
from html import unescape
from urllib.parse import quote, urlparse

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


BASE_URL = "https://creativemarket.com/"
NOT_FOUND_MARKER = "<title>Resource no longer available</title>"


def validate_creativemarket_shop(user: str) -> Result:
    url = f"{BASE_URL}{quote(user, safe='')}"

    def process(response) -> Result:
        if response.status_code == 410:
            if NOT_FOUND_MARKER in response.text:
                return Result.available()
            return Result.error("Creative Market 410 response missing not-found marker")

        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        match = re.search(
            r"var _jsConfig = (\{.*?\});\s*var APP", response.text, re.DOTALL
        )
        if not match:
            return Result.error("Creative Market shop data not found")

        try:
            config = json.loads(match.group(1))
        except json.JSONDecodeError:
            return Result.error("Invalid Creative Market shop data")

        shop = config.get("pageData")
        if not isinstance(shop, dict):
            return Result.error("Unexpected Creative Market shop payload")

        username = shop.get("username")
        if not isinstance(username, str) or username.casefold() != user.casefold():
            return Result.error("Creative Market returned a different user")

        if config.get("page_type") == "user_activity":
            if shop.get("shopExists") is False:
                return Result.available()
            return Result.error("Creative Market account has an inconsistent shop state")

        if config.get("page_type") != "user_shop" or shop.get("shopExists") is not True:
            return Result.error("Unexpected Creative Market shop payload")

        extra = {
            "name": shop.get("shopTitle"),
            "description": unescape(shop.get("userBio") or ""),
            "location": shop.get("userLocation"),
            "created": shop.get("shopCreatedDate"),
            "account_created": shop.get("userCreatedDate"),
            "id": shop.get("shopID"),
            "owner_id": shop.get("userID"),
            "followers": shop.get("numFollowers"),
            "following": shop.get("numFollowing"),
            "rating": shop.get("shopReviewRating"),
            "sales": shop.get("shopNumSales"),
            "featured": shop.get("isFeaturedBadgeEnabled"),
        }

        website = _url(shop.get("shopWebsite"))
        if website:
            extra["website"] = website

        for key, value in (
            ("products", shop.get("productResultData")),
            ("reviews", shop.get("shopReviews")),
            ("updates", shop.get("shopUpdates")),
        ):
            if isinstance(value, dict) and isinstance(value.get("pagination"), dict):
                extra[key] = value["pagination"].get("totalResults")

        product_data = shop.get("productResultData")
        products = product_data.get("products") if isinstance(product_data, dict) else None
        product_shop = (
            products[0].get("shop")
            if products and isinstance(products[0], dict)
            else None
        )
        if isinstance(product_shop, dict):
            extra.update(
                active=product_shop.get("is_active"),
                recommendation_percent=product_shop.get("recommendation_percent"),
                recommendations_up=product_shop.get("recommendations_up"),
                recommendations_down=product_shop.get("recommendations_down"),
            )

        for social in shop.get("socialLinks") or []:
            if not isinstance(social, dict) or not social.get("platform"):
                continue
            if link := _url(social.get("link")):
                extra[str(social["platform"]).lower()] = link

        return Result.taken(
            extra=extra,
            media={
                "avatar": shop.get("avatarUrl"),
                "banner": shop.get("bannerImage"),
                "about": shop.get("aboutImageUrl"),
            },
        )

    return impersonate_validate(
        url,
        process,
        warmup_url=BASE_URL,
        impersonate="chrome120",
        allow_redirects=True,
    )


def _url(value) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None
