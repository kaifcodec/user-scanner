import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://api.accounts.firefox.com/v1/account/status"
    show_url = "https://firefox.com"

    payload = {
        "email": email
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)", url=show_url)

            if response.status_code == 429:
                return Result.error("Rate limited by Firefox (429)", url=show_url)

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}", url=show_url)

            data = response.json()
            if not isinstance(data, dict):
                return Result.error("Unexpected response body format", url=show_url)

            exists = data.get("exists")
            if exists is True:
                return Result.taken(url=show_url)
            elif exists is False:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure", url=show_url)

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks", url=show_url)
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)

async def validate_firefox(email: str) -> Result:
    return await _check(email)
