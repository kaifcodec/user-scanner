from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


_URL = "https://cms.zadovoljstvozaposlenika.hr/api/auth/password/request-reset"
_NOT_FOUND = "The selected email is invalid."
_SENT = {"data": {"status": True}}


async def validate_pulser(email: str) -> Result:
    """Request a password reset when the email belongs to an account."""
    show_url = "https://pulser.hr"

    try:
        response = await impersonate_request_async(
            _URL,
            method="POST",
            json={"email": email},
            headers={"Accept": "application/json, text/plain, */*"},
        )
        data = response.json()
    except Exception as exc:
        return Result.error(exc, url=show_url)

    message = data.get("message") if isinstance(data, dict) else None
    if response.status_code == 422 and message == _NOT_FOUND:
        return Result.available(url=show_url)
    if response.status_code == 200 and data == _SENT:
        return Result.taken(url=show_url)
    return Result.error(
        f"Unexpected password reset response: {response.status_code}", url=show_url
    )
