import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://www.xda-developers.com/check-user-exists/"

    params = {
        'email': email,
        'subscribe': "true"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Referer': "https://www.xda-developers.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            data = response.json()
            exists = data.get("userExists")

            if exists is True:
                return Result.taken()

            if exists is False:
                return Result.available()

            return Result.error("Unexpected response body, report it on github")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out (XDA)")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (XDA)")
    except Exception as e:
        return Result.error(e)

async def validate_xda(email: str) -> Result:
    return await _check(email)
