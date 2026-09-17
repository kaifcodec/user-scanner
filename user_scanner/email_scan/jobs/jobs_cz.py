import re

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


_URL = "https://www.jobs.cz/obnova-hesla/"
_NOT_FOUND = "Zadaný e-mail není registrovaný."
_SENT = "Posíláme odkaz pro obnovení hesla"


async def validate_jobs_cz(email: str) -> Result:
    """Request a password reset when the email belongs to an account."""
    show_url = "https://www.jobs.cz"

    try:
        page = await impersonate_request_async(_URL)
        token = re.search(
            r'name="user_email\[_token\]" value="([^"]+)"', page.text
        )
        if not token:
            return Result.error("Could not find password reset token", url=show_url)

        response = await impersonate_request_async(
            _URL,
            method="POST",
            data={
                "user_email[email]": email,
                "user_email[submit]": "",
                "user_email[_token]": token.group(1),
            },
            allow_redirects=True,
        )
    except Exception as exc:
        return Result.error(exc, url=show_url)

    if response.status_code == 403:
        return Result.error("Rate limited by Jobs.cz", url=show_url)
    if response.status_code != 200:
        return Result.error(
            f"Unexpected password reset response: {response.status_code}",
            url=show_url,
        )
    if _NOT_FOUND in response.text:
        return Result.available(url=show_url)
    if _SENT in response.text:
        return Result.taken(url=show_url)
    return Result.error("Unexpected password reset response body", url=show_url)
