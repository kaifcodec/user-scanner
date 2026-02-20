import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://neocities.org"
    url = "https://neocities.org/create_validate"

    payload = {
        'field': "email",
        'value': email,
        'is_education': "false"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://neocities.org",
        'referer': "https://neocities.org/",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()

            if "error" in data:
                if "already exists" in data["error"]:
                    return Result.taken(url=show_url)
                return Result.error(f"Neocities error: {data['error']}")

            if data.get("result") == "ok":
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except Exception as e:
        return Result.error(e)


async def validate_neocities(email: str) -> Result:
    return await _check(email)
