import re

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


_URL = "https://www.seduo.sk/poslat-zabudnute-heslo"
_NOT_FOUND = "Zadaný e-mail neexistuje, skúste ho napísať znova."
_SENT = "Na váš e-mail sme odoslali odkaz na vytvorenie nového hesla."
_SSO = "Resetovanie hesla nie je povolené. Používateľ sa prihlasuje cez SSO."


async def validate_seduo_sk(email: str) -> Result:
    """Request a password reset when the email belongs to an account."""
    show_url = "https://www.seduo.sk"

    try:
        page = await impersonate_request_async(_URL)
        token = re.search(
            r'name="forgot_password\[_token\]"[^>]*value="([^"]+)"', page.text
        )
        if not token:
            return Result.error("Could not find password reset token", url=show_url)

        response = await impersonate_request_async(
            _URL,
            method="POST",
            data={
                "forgot_password[email]": email,
                "forgot_password[send]": "",
                "forgot_password[_token]": token.group(1),
            },
            allow_redirects=True,
        )
    except Exception as exc:
        return Result.error(exc, url=show_url)

    if response.status_code != 200:
        return Result.error(
            f"Unexpected password reset response: {response.status_code}", url=show_url
        )
    if _NOT_FOUND in response.text:
        return Result.available(url=show_url)
    if _SENT in response.text:
        return Result.taken(url=show_url)
    if _SSO in response.text:
        return Result.taken(extra={"auth_method": "Azure SSO"}, url=show_url)
    return Result.error("Unexpected password reset response body", url=show_url)
