"""Check Ravelry usernames through the login form with an invalid password."""

import re
import secrets
from html import unescape

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request
from user_scanner.core.result import Result

LOGIN_URL = "https://www.ravelry.com/account/login"


def validate_ravelry(user: str) -> Result:
    """The login form checks the account namespace; profiles require sign-in."""
    show_url = f"https://www.ravelry.com/people/{user}"
    try:
        page = impersonate_request(LOGIN_URL)
        token = re.search(r'name="authenticity_token"[^>]*value="([^"]+)"', page.text)
        if page.status_code != 200 or not token:
            return Result.error(
                f"Could not read Ravelry login form: HTTP {page.status_code}",
                url=show_url,
            )

        response = impersonate_request(
            LOGIN_URL,
            "POST",
            data={
                "authenticity_token": unescape(token.group(1)),
                "user[login]": user,
                "user[password]": secrets.token_urlsafe(32),
            },
        )
    except RequestException as exc:
        return Result.error(exc, url=show_url)

    if (
        response.status_code == 200
        and "Your password is incorrect\n</div>" in response.text
    ):
        return Result.taken(url=show_url)
    if (
        response.status_code == 404
        and "</strong> isn't a Ravelry user." in response.text
    ):
        return Result.available(url=show_url)
    return Result.error(
        f"Unexpected Ravelry login response: HTTP {response.status_code}",
        url=show_url,
    )
