import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.howtogeek.com/check-user-exists/"
    show_url = "https://www.howtogeek.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'Referer': "https://www.howtogeek.com/",
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
                return Result.error("Rate limited by How-To Geek (429)")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()

            # Use the userExists key for validation
            if data.get("userExists") is True:
                return Result.taken(url=show_url)

            elif data.get("userExists") is False:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_howtogeek(email: str) -> Result:
    return await _check(email)
