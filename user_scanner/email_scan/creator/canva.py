import json

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://www.canva.com/_ajax/authnflow/user-authentication-methods"
    show_url = "https://www.canva.com/"

    headers = {
        "Referer": "https://www.canva.com/login",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
    }

    payload = {
        "C": "Linux / Chrome",
        "A?": "E",
        "L": email,
    }

    try:
        response = await impersonate_request_async(
            url, "POST", data=json.dumps(payload), headers=headers, impersonate="chrome120"
        )

        if response.status_code == 403:
            return Result.error("Access forbidden / WAF blocked (403)")
        if response.status_code == 429:
            return Result.error("Rate limited by Canva (429)")
        if response.status_code != 200:
            return Result.error(f"Unexpected response status (HTTP {response.status_code})")

        raw_text = response.text
        start_idx = raw_text.find("{")
        end_idx = raw_text.rfind("}")
        if start_idx == -1 or end_idx == -1:
            return Result.error("Invalid JSON response from Canva")

        data = json.loads(raw_text[start_idx : end_idx + 1])
        action_type = data.get("B", {}).get("A?")

        # Action "A" corresponds to Login / Authenticate for existing users
        if action_type == "A":
            return Result.taken(url=show_url)

        # Action "B" corresponds to Sign up / Create account for new users
        if action_type == "B":
            return Result.available(url=show_url)

        return Result.error("Unknown response payload format")

    except Exception as e:
        return Result.error(str(e))

async def validate_canva(email: str) -> Result:
    return await _check(email)
