"""Silent Troc Vélo email registration check."""

import base64
import re

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.nextjs import iter_next_app_flight_chunks
from user_scanner.core.result import Result

SITE_URL = "https://www.troc-velo.com"
SIGNUP_URL = f"{SITE_URL}/fr-fr/creation-de-compte/particulier"
CHECK_URL = "https://api.troc-velo.com/api/users/check_email"
TOKEN_DATA_RE = re.compile(
    r'"apiCsrfToken"\s*:\s*"([^"]+)".*?'
    r'"routeIdentifier"\s*:\s*"([^"]+)".*?'
    r'"clientIp"\s*:\s*"([^"]+)"'
)


async def validate_trocvelo(email: str) -> Result:
    """Check registration availability without creating an account or sending email."""
    try:
        page = await impersonate_request_async(
            SIGNUP_URL, warmup_url=SITE_URL, allow_redirects=True
        )
        if page.status_code != 200:
            return Result.error(
                f"Unexpected signup status: {page.status_code}", url=SITE_URL
            )

        match = next(
            (
                match
                for chunk in iter_next_app_flight_chunks(page.text)
                if (match := TOKEN_DATA_RE.search(chunk))
            ),
            None,
        )
        if not match:
            return Result.error("Registration token not found", url=SITE_URL)

        encoded_token, route_identifier, client_ip = match.groups()
        encoded_token = encoded_token[24:-48]
        token = base64.urlsafe_b64decode(
            encoded_token + "=" * (-len(encoded_token) % 4)
        ).decode()

        response = await impersonate_request_async(
            CHECK_URL,
            method="POST",
            json={"email": email},
            headers={
                "Accept": "application/json, text/plain, */*",
                "Origin": SITE_URL,
                "Referer": f"{SITE_URL}/",
                "token-signature": token,
                "route-identifier": route_identifier,
                "ip-forward": client_ip,
            },
        )
    except (RequestException, ValueError) as exc:
        return Result.error(exc, url=SITE_URL)

    if response.status_code == 429:
        return Result.error("Rate limited; try again later", url=SITE_URL)
    if response.status_code != 200:
        return Result.error(
            f"Unexpected check status: {response.status_code}", url=SITE_URL
        )

    try:
        data = response.json()
    except ValueError:
        return Result.error("Unexpected check response", url=SITE_URL)
    match data:
        case {"exists": True}:
            return Result.taken(url=SITE_URL)
        case {"exists": False}:
            return Result.available(url=SITE_URL)
        case _:
            return Result.error("Email status was missing", url=SITE_URL)
