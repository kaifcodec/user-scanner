from urllib.parse import quote

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.nextjs import parse_next_pages_data
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

GEO_BLOCK_MARKER = "configured to block access from your country"


def validate_yaga_ee(user: str) -> Result:
    user = user.lower()
    url = f"https://www.yaga.ee/{quote(user, safe='')}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()

        if response.status_code != 200:
            # CloudFront fronts this shop and refuses whole countries outright;
            # that 403 says nothing about the handle.
            if response.status_code == 403 and GEO_BLOCK_MARKER in response.text:
                return Result.error("CloudFront blocks this country, the site is unreachable from here")

            return Result.error(
                f"Unexpected response status: {response.status_code}",
            )

        data = parse_next_pages_data(response.text)
        if data is None:
            return Result.error("Could not read Next.js data")

        page_props = data.get("props", {}).get("pageProps", {})
        shop = page_props.get("initialShop")

        if shop is None:
            return Result.available()

        if shop.get("activeSlug") != user:
            return Result.error("Unexpected shop slug")

        extra = {}
        owner = shop.get("owner") or {}
        if shop_id := shop.get("id"): extra["id"] = shop_id
        if name := shop.get("name"): extra["name"] = name
        if description := shop.get("description"): extra["description"] = description
        if first_name := owner.get("firstName"): extra["owner_first_name"] = first_name
        if last_name := owner.get("lastName"): extra["owner_last_name"] = last_name

        return Result.taken(extra=extra)

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=url,
        follow_redirects=True,
    )
