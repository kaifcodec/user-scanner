import re

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def validate_svenvaher(email: str) -> Result:
    """Loud: request Sven Vaher's password-reset verification email."""
    show_url = "https://svenvaher.ee/reset"
    try:
        page = await impersonate_request_async(show_url)
        secret = re.search(r'name="secret" value="([^"]+)"', page.text)
        if page.status_code != 200 or not secret:
            return Result.error("Could not obtain password-reset token", url=show_url)
        response = await impersonate_request_async(
            "https://svenvaher.ee/includes/ajax/core/forget_password.php",
            method="POST",
            data={"email": email, "secret": secret.group(1)},
            headers={"X-Requested-With": "XMLHttpRequest", "Referer": show_url},
        )
        data = response.json()
    except (RequestException, ValueError) as exc:
        return Result.error(exc, url=show_url)

    if response.status_code == 200 and isinstance(data, dict):
        if data.get("error") is True:
            if data.get("message") == (
                f"Vabandust, tundub, et {email} ei kuulu ühelegi kontole"
            ):
                return Result.available(url=show_url)
            if data.get("message") == "Palun sisestage kehtiv e-posti aadress":
                return Result.error("Invalid email format", url=show_url)
        callback = data.get("callback")
        if (
            not data.get("error")
            and isinstance(callback, str)
            and re.search(r"\bmodal\(\s*['\"]#forget-password-confirm['\"]", callback)
        ):
            return Result.taken(url=show_url)
    return Result.error(
        f"Unexpected password-reset response: {response.status_code}", url=show_url
    )
