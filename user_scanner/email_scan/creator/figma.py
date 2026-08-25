import urllib.parse

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    encoded_email = urllib.parse.quote(email)
    url = f"https://www.figma.com/api/session/available_auth_methods?email={encoded_email}&form_intent=sign_up"
    show_url = "https://www.figma.com/"

    headers = {
        "Referer": "https://www.figma.com/signup",
        "Accept": "application/json, text/plain, */*",
    }

    try:
        response = await impersonate_request_async(
            url, "GET", headers=headers, impersonate="chrome120"
        )

        if response.status_code == 403:
            return Result.error("Access forbidden / WAF blocked (403)")
        if response.status_code == 429:
            return Result.error("Rate limited by Figma (429)")
        if response.status_code != 200:
            return Result.error(f"Unexpected response status (HTTP {response.status_code})")

        data = response.json()
        if data.get("error") is True:
            return Result.error(f"Figma API returned error: {data.get('message')}")

        meta = data.get("meta", {})
        available_methods = meta.get("available_methods", [])

        # When the user is already registered, "sign_in" is listed in available_methods
        if "sign_in" in available_methods:
            return Result.taken(url=show_url)

        # When the user is not registered, "sign_up" is listed in available_methods
        if "sign_up" in available_methods:
            return Result.available(url=show_url)

        return Result.error("Unknown response payload format")

    except Exception as e:
        return Result.error(str(e))

async def validate_figma(email: str) -> Result:
    return await _check(email)
