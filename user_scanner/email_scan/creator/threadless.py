"""Threadless email registration check via the public Artist Shops signup form."""

import re

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result

SIGNUP_URL = "https://profile.threadless.com/artist/shops/"
CSRF_RE = re.compile(r"name=['\"]csrfmiddlewaretoken['\"]\s+value=['\"]([^'\"]+)")


async def validate_threadless(email: str) -> Result:
    """Check Threadless without creating an account or sending email."""
    show_url = "https://www.threadless.com"

    try:
        page = await impersonate_request_async(SIGNUP_URL, allow_redirects=True)
        token = CSRF_RE.search(page.text)
        if page.status_code != 200 or not token:
            return Result.error(
                f"Could not read Threadless signup form (HTTP {page.status_code})",
                url=show_url,
            )

        response = await impersonate_request_async(
            SIGNUP_URL,
            "POST",
            headers={"x-requested-with": "XMLHttpRequest"},
            data={
                "validate": "true",
                "email": email,
                "csrfmiddlewaretoken": token.group(1),
            },
        )
        if response.status_code != 200:
            return Result.error(
                f"Unexpected Threadless response: HTTP {response.status_code}",
                url=show_url,
            )

    except RequestException as exc:
        return Result.error(exc, url=show_url)

    try:
        data = response.json()
    except ValueError:
        return Result.error("Invalid Threadless response", url=show_url)

    if data.get("is_valid") is False:
        return Result.taken(url=show_url)
    if data.get("is_valid") is True:
        return Result.available(url=show_url)
    return Result.error("Unexpected Threadless response", url=show_url)
