from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.freelancer.com/api/users/0.1/users/check?compact=true&new_errors=true"
    show_url = "https://freelancer.com"

    payload = {
        "user": {
            "email": email
        }
    }

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://www.freelancer.com',
    }

    try:
        response = await impersonate_request_async(
            url,
            method="POST",
            json=payload,
            headers=headers,
        )

        if response.status_code == 409 and "EMAIL_ALREADY_IN_USE" in response.text:
            return Result.taken(url=show_url)

        elif response.status_code == 200:
            return Result.available(url=show_url)

        return Result.error(
            f"Unexpected status code {response.status_code} or rate limit",
            url=show_url,
        )

    except Exception as e:
        return Result.error(e, url=show_url)


async def validate_freelancer(email: str) -> Result:
    return await _check(email)
