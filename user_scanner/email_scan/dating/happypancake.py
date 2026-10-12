from urllib.parse import quote

import httpx

from user_scanner.core.helpers import get_global_timeout, get_proxy
from user_scanner.core.result import Result


async def validate_happypancake(email: str) -> Result:
    """Check HappyPancake Sweden email availability without sending mail."""
    show_url = "https://www.happypancake.se/signup"
    url = "https://api.happypancake.se/accounts/validateemail/" + quote(email, safe="")
    try:
        async with httpx.AsyncClient(
            proxy=get_proxy(), timeout=get_global_timeout() or 15.0
        ) as client:
            response = await client.get(url)
        if response.status_code != 200:
            return Result.error(
                f"Unexpected validation status: {response.status_code}", url=show_url
            )
        data = response.json()
        if isinstance(data, dict):
            if data.get("valid") is True and data.get("message") is None:
                return Result.available(url=show_url)
            if data.get("valid") is False and data.get("message") == "in-use":
                return Result.taken(url=show_url)
            if data.get("message") == "invalid-format":
                return Result.error("Invalid HappyPancake email format", url=show_url)
        return Result.error("Unexpected email validation response", url=show_url)
    except (httpx.HTTPError, ValueError) as exc:
        return Result.error(exc, url=show_url)
