from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


_URL = "https://www.cvonline.lt/api/v1/authentication/password/forgot-password"
_NOT_FOUND = {"errorType": "RESOURCE_NOT_FOUND", "message": "Resource not found."}


async def validate_cvonline_lt(email: str) -> Result:
    """Request a password reset when the email belongs to an account."""
    show_url = "https://www.cvonline.lt"

    try:
        response = await impersonate_request_async(
            _URL, method="POST", json={"email": email}
        )
    except Exception as exc:
        return Result.error(exc, url=show_url)

    if response.status_code == 404:
        try:
            if response.json() == _NOT_FOUND:
                return Result.available(url=show_url)
        except ValueError:
            pass
    if response.status_code == 200 and not response.content:
        return Result.taken(url=show_url)
    return Result.error(
        f"Unexpected password reset response: {response.status_code}", url=show_url
    )
