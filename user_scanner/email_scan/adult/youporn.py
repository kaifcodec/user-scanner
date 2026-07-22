import httpx
import re
from user_scanner.core.helpers import is_valid_email
from user_scanner.core.result import Result

RATE_LIMITED_MSG = "Rate limited, wait for a few minutes"


async def _check(email: str) -> Result:
    base_url = "https://www.youporn.com"
    show_url = "https://youporn.com"
    register_url = f"{base_url}/register"
    check_api = f"{base_url}/register/verify_email"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": base_url,
        "Referer": register_url,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    async with httpx.AsyncClient(http2=True, follow_redirects=True, timeout=15.0) as client:
        try:
            landing_resp = await client.get(register_url, headers=headers)
            token_match = re.search(
                r'page_params\.token\s*=\s*"([^"]+)"', landing_resp.text
            )

            if not token_match:
                return Result.error("Failed to extract dynamic token from HTML")

            token = token_match.group(1)

            params = {"token": token}
            payload = {"token": token, "email": email}

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

            if data.get("success") is True:
                return Result.available(url=show_url)

            messages = data.get("messages", [])
            message = " ".join(messages) if isinstance(messages, list) else str(messages)

            # A well-formed address that fails the requirements check is YouPorn's
            # way of reporting an existing account rather than saying it's taken.
            if "does not meet our registration requirements" in message:
                if is_valid_email(email):
                    return Result.taken(url=show_url)
                return Result.available(url=show_url, reason=message)

            # A stale or over-used token answers "Not available." instead of a verdict.
            if "not available" in message.lower():
                return Result.error(RATE_LIMITED_MSG)

            return Result.error(f"Unexpected API response: {message}")

        except Exception as e:
            return Result.error(e)


async def validate_youporn(email: str) -> Result:
    return await _check(email)
