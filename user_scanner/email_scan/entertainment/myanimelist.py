import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    show_url = "https://myanimelist.net"
    url = "https://myanimelist.net/signup/email/validate"

    payload = {
        'email': email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://myanimelist.net",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://myanimelist.net/register.php?",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()
            errors = data.get("errors", [])
            resp_data = data.get("data")

            if errors and any("already have an account" in err.get("message", "") for err in errors):
                return Result.taken(url=show_url)

            elif isinstance(resp_data, list) and len(resp_data) == 0:
                return Result.available(url=show_url)

            else:
                return Result.error("Unexpected response body structure, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)

async def validate_myanimelist(email: str) -> Result:
    return await _check(email)
