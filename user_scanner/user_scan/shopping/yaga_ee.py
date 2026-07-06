import html
import json
import re
from urllib.parse import quote

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.DOTALL,
)
UNSAFE_PATH_RE = re.compile(r"[/#?\x00-\x1f\x7f]")


def _extract_next_data(response_text: str) -> dict | None:
    match = NEXT_DATA_RE.search(response_text)
    if not match:
        return None

    return json.loads(html.unescape(match.group(1)))


def _shop_extra(shop: dict) -> dict:
    owner = shop.get("owner") or {}
    extra = {
        "id": shop.get("id"),
        "name": shop.get("name"),
        "description": shop.get("description"),
        "owner_first_name": owner.get("firstName") or owner.get("first_name"),
        "owner_last_name": owner.get("lastName") or owner.get("last_name"),
    }
    return {key: value for key, value in extra.items() if value}


def _validate_yaga(user: str, base_url: str) -> Result:
    user = user.strip().lower()
    url = f"{base_url}/{quote(user, safe='')}"

    if not user:
        return Result.error("Username cannot be empty", url=url)

    if UNSAFE_PATH_RE.search(user):
        return Result.error("Username contains unsafe URL path characters", url=url)

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        if response.status_code != 200:
            return Result.error(
                f"Unexpected response status: {response.status_code}",
            )

        try:
            data = _extract_next_data(response.text)
        except json.JSONDecodeError:
            return Result.error("Could not parse Next.js data")

        if data is None:
            return Result.error("Could not find Next.js data")

        page_props = data.get("props", {}).get("pageProps", {})
        shop = page_props.get("initialShop")

        if shop is None:
            return Result.available()

        if not isinstance(shop, dict):
            return Result.error("Unexpected shop data")

        if shop.get("activeSlug") != user:
            return Result.error("Unexpected shop slug")

        return Result.taken(extra=_shop_extra(shop))

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=url,
        follow_redirects=True,
    )


def validate_yaga_ee(user: str) -> Result:
    return _validate_yaga(user, "https://www.yaga.ee")
