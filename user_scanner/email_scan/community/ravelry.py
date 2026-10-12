"""Ravelry email recovery probe. Sends email and requires --allow-loud in scans."""

import re
from html import unescape

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result

FORM_URL = "https://www.ravelry.com/account/forgot"
REMIND_URL = "https://www.ravelry.com/account/remind"


async def validate_ravelry(email: str) -> Result:
    """Send a recovery email if registered; direct library calls also send email."""
    try:
        page = await impersonate_request_async(FORM_URL, params={"forgot": "both"})
        token = re.search(r'name="authenticity_token"[^>]*value="([^"]+)"', page.text)
        if page.status_code != 200 or not token:
            return Result.error(
                f"Could not read Ravelry recovery form: HTTP {page.status_code}",
                url=REMIND_URL,
            )

        response = await impersonate_request_async(
            REMIND_URL,
            "POST",
            data={
                "authenticity_token": unescape(token.group(1)),
                "forgot": "both",
                "email": email,
                "g-recaptcha-response": "",
            },
            allow_redirects=True,
        )
    except RequestException as exc:
        return Result.error(exc, url=REMIND_URL)

    if response.status_code == 200:
        if (
            "We've emailed a link that you can use to get back into your account."
            in response.text
        ):
            return Result.taken(url=REMIND_URL)
        if "We couldn't find an account with this email address." in response.text:
            return Result.available(url=REMIND_URL)
    return Result.error(
        f"Unexpected Ravelry recovery response: HTTP {response.status_code}",
        url=REMIND_URL,
    )
