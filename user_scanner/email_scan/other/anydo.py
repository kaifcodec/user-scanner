import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://sm-prod2.any.do/check_email"
    show_url = "https://any.do"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Content-Type": "application/json; charset=UTF-8",
        "Origin": "https://desktop.any.do",
        "Referer": "https://desktop.any.do/",
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                content=json.dumps(payload),
                headers=headers
            )

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if response.status_code == 429:
                return Result.error("Rate limited by Any.do (429)")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()

            if data.get("user_exists") is True:
                return Result.taken(url=show_url)

            elif data.get("user_exists") is False:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)

async def validate_anydo(email: str) -> Result:
    return await _check(email)
