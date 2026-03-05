import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://www.komoot.com"
    url = "https://www.komoot.com/v1/signin"

    payload = {
        "email": email,
        "reason": "header",
        "new_tab": False
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': "?1",
        'origin': "https://www.komoot.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.komoot.com/signin?referrer=www.google.com&reason=header",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            status = response.status_code

            if status == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if status == 200:
                data = response.json()
                response_type = data.get("type")

                if response_type == "login":
                    return Result.taken(url=show_url)

                if response_type == "register":
                    return Result.available(url=show_url)

            if status == 429:
                return Result.error("Rate limited by Komoot")

            return Result.error(f"Unexpected status code: {status}")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except Exception as e:
        return Result.error(e)


async def validate_komoot(email: str) -> Result:
    return await _check(email)
