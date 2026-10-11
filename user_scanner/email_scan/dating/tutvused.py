import html

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.helpers import EMAIL_RE
from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def validate_tutvused(email: str) -> Result:
    """Loud: request a Tutvused password-reset email through its public form API."""
    show_url = "https://tutvused.net/"
    if not EMAIL_RE.fullmatch(email):
        return Result.error("Invalid email format", url=show_url)
    try:
        response = await impersonate_request_async(
            "https://tutvused.net/wp-json/hivepress/v1/users/request-password/",
            method="POST",
            data={"username_or_email": email},
        )
        data = response.json()
    except (RequestException, ValueError) as exc:
        return Result.error(exc, url=show_url)

    if isinstance(data, dict):
        account = data.get("data")
        if (
            response.status_code == 200
            and isinstance(account, dict)
            and type(account.get("id")) is int
            and account["id"] > 0
        ):
            return Result.taken(url=show_url)
        error = data.get("error")
        if isinstance(error, dict):
            errors = error.get("errors")
            if isinstance(errors, list) and len(errors) == 1 and isinstance(errors[0], dict):
                message = html.unescape(str(errors[0].get("message", "")))
                if (
                    response.status_code == 404
                    and message == "User with this email doesn't exist."
                ):
                    return Result.available(url=show_url)
                if (
                    response.status_code == 401
                    and message == "Please check your email to activate your account."
                ):
                    return Result.taken("Account requires email activation", url=show_url)
    return Result.error(
        f"Unexpected password-reset response: {response.status_code}", url=show_url
    )
