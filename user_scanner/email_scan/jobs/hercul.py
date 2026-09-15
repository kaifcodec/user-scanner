from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


_API = "https://api.hercul.hr/api/auth"


async def validate_hercul(email: str) -> Result:
    """Request a password reset when the email belongs to an account."""
    show_url = "https://app.hercul.hr"

    try:
        availability = await impersonate_request_async(
            f"{_API}/email-available/{quote(email, safe='')}"
        )
        data = availability.json()
        is_available = data.get("isAvailable") if isinstance(data, dict) else None
        if availability.status_code != 200 or not isinstance(is_available, bool):
            return Result.error(
                f"Unexpected email availability response: {availability.status_code}",
                url=show_url,
            )
        if is_available:
            return Result.available(url=show_url)

        response = await impersonate_request_async(
            f"{_API}/users/reset-password",
            method="POST",
            json={"email": email},
        )
    except Exception as exc:
        return Result.error(exc, url=show_url)

    if response.status_code == 200 and not response.content:
        return Result.taken(url=show_url)
    return Result.error(
        f"Unexpected password reset response: {response.status_code}", url=show_url
    )
