import contextlib

import httpx

from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    """
    Checks whether a given email is registered on Dropbox.

    The check has two steps:

    1. Retrieve CSRF token (is set as a cookie with name "t").
    2. Use the check_user_with_email_exists endpoint of Dropbox's API to retreive the result.

    The API also returns whether the given email is registered as a recovery email and whether it has a passkey.
    """

    show_url = "https://www.dropbox.com"
    check_user_url = f"{show_url}/2/account/check_user_with_email_exists"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0",
        "Referer": show_url,
        "Origin": show_url,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        # 1. Retrieve the CSRF token
        csrf_token_retrieval_response = await client.get(show_url, headers=headers)

        if csrf_token_retrieval_response.status_code != 200:
            return Result.error(
                f"Failed to access the {show_url}: {csrf_token_retrieval_response.status_code}"
            )

        # Dropbox sets the CSRF token as the "t" cookie. The same value is also mirrored in "__Host-js_csrf".
        csrf_token = client.cookies.get("t")
        if not csrf_token:
            return Result.error("CSRF token not retrieved")

        # 2. Retrieve the information from Dropbox's API
        headers["X-CSRF-Token"] = csrf_token
        payload = {"email": email}
        response = await client.post(check_user_url, headers=headers, json=payload)

    if response.status_code != 200:
        reason = None
        with contextlib.suppress(ValueError):
            data = response.json()
            # For example, with invalid CSRF token the API returns this JSON:
            # {"error":{".tag":"invalid_csrf_token"},"error_summary":"invalid_csrf_token/"}
            reason = data.get("error", {}).get("error_summary")
        return Result.error(
            f"HTTP {response.status_code}" + (f": {reason}" if reason else "")
        )

    # Valid response looks like this: {"exists":false,"exists_as_recovery_email":false,"has_passkey":false}
    try:
        data = response.json()
    except ValueError:
        return Result.error(f"HTTP {response.status_code} but didn't retrieve JSON")
    exists = data.get("exists")
    exists_as_recovery_email = data.get("exists_as_recovery_email")
    has_passkey = data.get("has_passkey")

    for value in (exists, exists_as_recovery_email, has_passkey):
        if not isinstance(value, bool):
            return Result.error(
                "Failed to check, the response structure may have changed. Please create Github issue."
            )

    # Email is associated with a Dropbox account as primary
    if exists:
        return Result.taken(
            extra={
                "exists_as_recovery_email": exists_as_recovery_email,
                "has_passkey": has_passkey,
            },
            url=show_url,
        )

    # Email is associated with a Dropbox account as recovery, primary email of one account cannot be used as recovery for another account
    if exists_as_recovery_email:
        return Result.taken(
            extra={"exists_as_recovery_email": exists_as_recovery_email}, url=show_url
        )

    # Email is not associated with any Dropbox account
    return Result.available(url=show_url)


async def validate_dropbox(email: str) -> Result:
    return await _check(email)
