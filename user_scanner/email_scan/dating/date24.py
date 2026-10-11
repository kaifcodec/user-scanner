import re

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.helpers import EMAIL_RE
from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def validate_date24(email: str) -> Result:
    """Loud: submit Date24's username-or-email password-reset form."""
    show_url = "https://date24.ee/password"
    if not EMAIL_RE.fullmatch(email):
        return Result.error("Invalid email format", url=show_url)
    try:
        page = await impersonate_request_async(show_url)
        token = re.search(r'name="reset\[_csrf_token\]" value="([^"]+)"', page.text)
        if page.status_code != 200 or not token:
            return Result.error("Could not obtain password-reset token", url=show_url)
        response = await impersonate_request_async(
            show_url,
            method="POST",
            data={"reset[_csrf_token]": token.group(1), "reset[username]": email},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json",
                "Referer": show_url,
            },
        )
        data = response.json()
    except (RequestException, ValueError) as exc:
        return Result.error(exc, url=show_url)

    if response.status_code == 200 and isinstance(data, dict):
        if data.get("result") == "ok":
            return Result.taken(url=show_url)
        if data.get("result") == "error" and data.get("errors") == {
            "reset[username]": (
                "Sisestatud andmed on valed. Palun kontrolli, kas Sinu poolt "
                "sisestatud kasutajatunnus ja/või parool on õige."
            )
        }:
            return Result.available(url=show_url)
    return Result.error(
        f"Unexpected password-reset response: {response.status_code}", url=show_url
    )
