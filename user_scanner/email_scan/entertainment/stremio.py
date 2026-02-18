import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://stremio.com"
    url = "https://api.strem.io/api/login"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'Origin': "https://www.stremio.com",
        'Referer': "https://www.stremio.com/",
        'Accept-Language': "en-US,en;q=0.9",
    }

    payload = {
        "authKey": None,
        "email": email,
        "password": "wrongpassword123"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                error_data = data.get("error", {})

                if error_data.get("wrongPass") is True:
                    return Result.taken(url=show_url)
                elif error_data.get("wrongEmail") is True:
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_stremio(email: str) -> Result:
    return await _check(email)
