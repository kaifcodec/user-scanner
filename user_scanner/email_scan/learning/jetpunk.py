import httpx

from user_scanner.core.helpers import get_global_timeout, get_proxy
from user_scanner.core.result import Result


async def validate_jetpunk(email: str) -> Result:
    """Request a password reset. Registered accounts receive an email."""
    url = "https://www.jetpunk.com/api/send-forgot-password.php"
    show_url = "https://www.jetpunk.com"

    try:
        async with httpx.AsyncClient(
            timeout=get_global_timeout() or 15.0,
            proxy=get_proxy(),
        ) as client:
            response = await client.post(
                url,
                data={"email": email},
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 Chrome/141.0.0.0 Safari/537.36",
                },
            )
        if response.status_code != 200:
            return Result.error(
                f"Unexpected password reset response: {response.status_code}",
                url=show_url,
            )
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return Result.error(exc, url=show_url)

    if data.get("success") is True:
        return Result.taken(url=show_url)
    if (
        data.get("success") is False
        and data.get("err") == "No user with that e-mail address"
    ):
        return Result.available(url=show_url)
    return Result.error("Unexpected password reset response", url=show_url)
