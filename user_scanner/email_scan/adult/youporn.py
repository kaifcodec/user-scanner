import httpx
import re
import secrets
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

            async def check(address: str) -> dict | Result:
                response = await client.post(
                    check_api,
                    params={"token": token},
                    headers=headers,
                    data={"token": token, "email": address},
                )

                if response.status_code == 429:
                    return Result.error(RATE_LIMITED_MSG)

                if response.status_code != 200:
                    return Result.error(f"HTTP Error: {response.status_code}")

                return response.json()

            data = await check(email)
            if isinstance(data, Result):
                return data

            if data.get("success") is True:
                return Result.available(url=show_url)

            messages = data.get("messages", [])
            message = " ".join(messages) if isinstance(messages, list) else str(messages)

            if "does not meet our registration requirements" in message:
                domain = email.rsplit("@", 1)[-1]
                probe = await check(f"{secrets.token_hex(16)}@{domain}")
                if isinstance(probe, Result):
                    return probe
                probe_messages = probe.get("messages", [])
                probe_message = (
                    " ".join(probe_messages)
                    if isinstance(probe_messages, list)
                    else str(probe_messages)
                )
                if "does not meet our registration requirements" in probe_message:
                    return Result.available(url=show_url, reason=message)
                if "not available" in probe_message.lower():
                    return Result.error(RATE_LIMITED_MSG)
                return Result.taken(url=show_url)

            # A stale or over-used token answers "Not available." instead of a verdict.
            if "not available" in message.lower():
                return Result.error(RATE_LIMITED_MSG)

            return Result.error(f"Unexpected API response: {message}")

        except Exception as e:
            return Result.error(e)


async def validate_youporn(email: str) -> Result:
    return await _check(email)
