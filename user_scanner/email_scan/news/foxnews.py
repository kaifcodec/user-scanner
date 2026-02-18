import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent

async def _check(email: str) -> Result:
    url = "https://id.fox.com/status/v1/status"
    
    params = {
        'email': email
    }

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "*/*",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'x-api-key': "049f8b7844b84b9cb5f830f28f08648c",
        'origin': "https://auth.fox.com",
        'referer': "https://auth.fox.com/",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()
            found = data.get("found")

            if found is True:
                return Result.taken()
            
            elif found is False:
                return Result.available()

            else:
                return Result.error("Unexpected response body structure, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)

async def validate_foxnews(email: str) -> Result:
    return await _check(email)
