import httpx
import re
from user_scanner.core.helpers import is_valid_email
from user_scanner.core.result import Result

RATE_LIMITED_MSG = "Rate limited, wait for a few minutes"


async def _check(email: str) -> Result:
    base_url = "https://www.redtube.com"
    show_url = "https://redtube.com"
    register_url = f"{base_url}/register"
    check_api = f"{base_url}/user/create_account_check"

    headers = {
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "origin": base_url,
        "referer": register_url,
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    async with httpx.AsyncClient(http2=True, follow_redirects=True, timeout=15.0) as client:
        try:
            landing_resp = await client.get(register_url, headers=headers)
            # The token is assigned to page_params.token and ends with a literal
            # dot that is part of the value — capturing anything but the quotes
            # keeps it intact (dropping the dot invalidates the token).
            token_match = re.search(
                r'page_params\.token\s*=\s*"([^"]+)"', landing_resp.text
            )

            if not token_match:
                return Result.error("Failed to extract dynamic token from HTML")

            token = token_match.group(1)

            params = {"token": token}
            payload = {
                "token": token,
                "check_what": "email",
                "email": email,
            }

            response = await client.post(
                check_api,
                params=params,
                headers=headers,
                data=payload,
            )

            if response.status_code == 429:
                return Result.error(RATE_LIMITED_MSG)

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()

            # An anti-abuse throttle answers with a bare "NOK" / "NOK <n>" string
            # instead of the usual JSON object.
            if not isinstance(data, dict):
                return Result.error(RATE_LIMITED_MSG)

            status = data.get("email")
            error_msg = data.get("error_message", "")

            if status == "create_account_passed" and error_msg == "":
                return Result.available(url=show_url)

            if status == "create_account_failed":
                if "already registered" in error_msg:
                    return Result.taken(url=show_url)
                # For a well-formed address, RedTube reports an existing account
                # by refusing registration rather than saying it's taken.
                if "does not meet our registration requirements" in error_msg and is_valid_email(email):
                    return Result.taken(url=show_url)
                return Result.available(url=show_url, reason=error_msg)

            return Result.error(f"Unexpected API response: {status}: {error_msg}")

        except Exception as e:
            return Result.error(e)


async def validate_redtube(email: str) -> Result:
    return await _check(email)
