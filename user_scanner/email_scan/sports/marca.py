import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://marca.com"
    url = f"https://seguro.marca.com/ueregistro/v2/usuarios/comprobacion/{email}/2"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Origin': "https://www.marca.com",
        'Referer': "https://www.marca.com/",
        'Accept-Language': "en-US,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)

            if response.status_code in [200, 404]:
                data = response.json()
                status = data.get("status")

                if status == "OK":
                    return Result.taken(url=show_url)
                elif status == "NOK":
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_marca(email: str) -> Result:
    return await _check(email)
