import json
import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


NEXT_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def _extract_next_data(html: str) -> dict | None:
    match = NEXT_DATA_PATTERN.search(html)
    if not match:
        return None

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None

    return data if isinstance(data, dict) else None


def validate_daily_dev(user):
    url = f"https://app.daily.dev/{user}"
    show_url = f"https://app.daily.dev/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
    }

    def process(response):
        next_data = _extract_next_data(response.text)
        if next_data is None:
            return Result.error(
                "Could not read __NEXT_DATA__ payload, report it via GitHub issues."
            )

        page_props = next_data.get("props", {}).get("pageProps", {})
        user_data = page_props.get("user")

        if isinstance(user_data, dict):
            if user_data.get("id") and user_data.get("name"):
                return Result.taken()

        if page_props.get("noindex") is True:
            return Result.available()

        return Result.error(
            "Unexpected daily.dev payload shape, report it via GitHub issues."
        )

    return generic_validate(url, process, show_url=show_url, headers=headers)
