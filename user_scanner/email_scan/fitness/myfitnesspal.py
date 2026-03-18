import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.myfitnesspal.com/api/idm/user-exists"
    show_url = "https://www.myfitnesspal.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'Referer': "https://www.myfitnesspal.com/account/create",
        'Accept-Language': "en-US,en;q=0.9",
        'Priority': "u=1, i"
    }

    params = {
        'email': email
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if response.status_code == 429:
                return Result.error("Rate limited by MyFitnessPal (429)")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()

            # Use the emailExists key for validation
            if data.get("emailExists") is True:
                return Result.taken(url=show_url)

            elif data.get("emailExists") is False:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_myfitnesspal(email: str) -> Result:
    return await _check(email)
