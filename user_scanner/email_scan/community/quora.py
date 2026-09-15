import re

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result

SHOW_URL = "https://www.quora.com"
QUERY_NAME = "SignupEmailForm_validateEmail_Query"
QUERY_HASH = "1db80096407be846d5581fe1b42b12fd05e0b40a5d3095ed40a0b4bd28f49fe7"


async def validate_quora(email: str) -> Result:
    """Quiet signup validation probe. It sends no email."""
    try:
        page = await impersonate_request_async(SHOW_URL, allow_redirects=True)
        formkey = re.search(r'"formkey":\s*"([a-f0-9]+)"', page.text)
        if page.status_code != 200 or not formkey:
            return Result.error(
                f"Could not load Quora login page: {page.status_code}",
                url=SHOW_URL,
            )

        response = await impersonate_request_async(
            f"{SHOW_URL}/graphql/gql_para_POST",
            "POST",
            params={"q": QUERY_NAME},
            headers={"quora-formkey": formkey.group(1)},
            json={
                "queryName": QUERY_NAME,
                "variables": {"email": email},
                "extensions": {"hash": QUERY_HASH},
            },
        )
        if response.status_code != 200:
            return Result.error(
                f"Unexpected Quora response: {response.status_code}",
                url=SHOW_URL,
            )

        state = (response.json().get("data") or {}).get("validateEmail")
        if state in {"IN_USE", "NOT_CONFIRMED"}:
            confirmed = state == "IN_USE"
            return Result.taken(url=SHOW_URL, extra={"email_confirmed": confirmed})
        if state == "OK":
            return Result.available(url=SHOW_URL)
        return Result.error(f"Unexpected Quora signup state: {state}", url=SHOW_URL)
    except (RequestException, ValueError, AttributeError) as exc:
        return Result.error(exc, url=SHOW_URL)
