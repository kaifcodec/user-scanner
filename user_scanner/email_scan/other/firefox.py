import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://api.accounts.firefox.com/v1/account/status"
    show_url = "https://firefox.com"

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, data=payload)

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if response.status_code == 429:
                return Result.error("Rate limited by Firefox (429)")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            text = response.text.lower()

            if "true" in text:
                return Result.taken(url=show_url)

            elif "false" in text:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)

async def validate_firefox(email: str) -> Result:
    return await _check(email)
