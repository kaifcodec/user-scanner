from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def validate_flirtic(email: str) -> Result:
    """Loud: request a password-reset email for a registered Flirtic account."""
    show_url = "https://www.flirtic.ee/lost_password"
    try:
        response = await impersonate_request_async(
            show_url,
            method="POST",
            data={"action": "send", "email": email},
            allow_redirects=True,
        )
    except (RequestException, ValueError) as exc:
        return Result.error(exc, url=show_url)

    if response.status_code != 200:
        return Result.error(
            f"Unexpected password-reset status: {response.status_code}", url=show_url
        )

    if (
        "Saatsime Sulle e-kirja instruktsiooniga, kuidas salasõna vahetada."
        in response.text
    ):
        return Result.taken(url=show_url)
    if "Tundmatu meiliaadress!" in response.text:
        return Result.available(url=show_url)
    return Result.error("Unexpected password-reset response", url=show_url)
