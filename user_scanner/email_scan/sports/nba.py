import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    show_url = "https://www.nba.com"
    url = "https://identity.nba.com/api/v1/profile/registrationStatus"

    payload = {
        "email": email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'x-client-platform': "web",
        'origin': "https://www.nba.com",
        'referer': "https://www.nba.com/",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            status = response.status_code

            if status == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if status == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("data", {}).get("isFull") is True:
                    return Result.taken(url=show_url)

            if status == 400:
                data = response.json()
                if "INVALID_PROFILE_STATUS" in data.get("errorCodes", []) or "Profile not found" in data.get("data", {}).get("message", ""):
                    return Result.available(url=show_url)

            if status == 429:
                return Result.error("Rate limited by NBA")

            return Result.error(f"Unexpected status code: {status}")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except Exception as e:
        return Result.error(e)

async def validate_nba(email: str) -> Result:
    return await _check(email)
