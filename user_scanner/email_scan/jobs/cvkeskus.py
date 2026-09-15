import re

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


_URL = "https://www.cvkeskus.ee/remind/username"
_NOT_FOUND = "Sisestatud e-posti aadress puudub meie süsteemis."
_MULTIPLE_ACCOUNTS = "Selle e-posti aadressiga on seotud mitu kontot."
_REMINDER_SENT = "Saatsime Sinu kasutajanime meeldetuletuse e-postile:"


async def validate_cvkeskus(email: str) -> Result:
    """Send a username reminder when the email belongs to one account."""
    show_url = "https://www.cvkeskus.ee"

    try:
        page = await impersonate_request_async(_URL)
        if page.status_code != 200 or 'id="reminderForm"' not in page.text:
            return Result.error(
                f"Unexpected reminder page response: {page.status_code}",
                url=show_url,
            )

        token = re.search(
            r"name=['\"]csrf_token['\"] value=['\"]([^'\"]+)", page.text
        )
        if not token:
            return Result.error("Could not find reminder CSRF token", url=show_url)

        response = await impersonate_request_async(
            _URL,
            method="POST",
            data={"csrf_token": token.group(1), "email": email},
            headers={"Referer": _URL},
        )
    except Exception as exc:
        return Result.error(exc, url=show_url)

    if response.status_code != 200:
        return Result.error(
            f"Unexpected reminder response: {response.status_code}", url=show_url
        )
    if _NOT_FOUND in response.text:
        return Result.available(url=show_url)
    if _MULTIPLE_ACCOUNTS in response.text:
        return Result.taken(url=show_url, extra={"multiple_accounts": True})
    if _REMINDER_SENT in response.text:
        return Result.taken(url=show_url, extra={"multiple_accounts": False})
    return Result.error("Unexpected reminder response body", url=show_url)
