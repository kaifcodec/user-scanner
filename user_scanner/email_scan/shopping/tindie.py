from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def validate_tindie(email: str) -> Result:
    signup_url = "https://www.tindie.com/accounts/signup/"
    check_url = "https://www.tindie.com/accounts/check_email/"
    show_url = "https://www.tindie.com/"

    try:
        landing = await impersonate_request_async(signup_url)
        if landing.status_code != 200:
            return Result.error(
                f"Unexpected signup status: {landing.status_code}", url=show_url
            )

        token = landing.cookies.get("csrftoken")
        if not token:
            return Result.error("CSRF token not found", url=show_url)

        response = await impersonate_request_async(
            check_url,
            method="POST",
            data={"email": email},
            headers={
                "Referer": signup_url,
                "X-CSRFToken": token,
            },
        )
    except RequestException as exc:
        return Result.error(exc, url=show_url)

    if response.status_code == 429:
        return Result.error("Rate limited; try again later", url=show_url)
    if response.status_code != 200:
        return Result.error(
            f"Unexpected check status: {response.status_code}", url=show_url
        )

    try:
        data = response.json()
    except ValueError:
        return Result.error("Invalid email response", url=show_url)

    match data:
        case {"valid": False, "errors": ["Email already registered!"]}:
            return Result.taken(url=show_url)
        case {"valid": True, "errors": [], "message": "Email available!"}:
            return Result.available(url=show_url)
        case {"errors": [error, *_]}:
            return Result.error(str(error), url=show_url)
        case _:
            return Result.error("Unexpected email response", url=show_url)
