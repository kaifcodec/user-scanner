import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://account.envato.com/api/public/validate_email"
    show_url = "https://account.envato.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': "application/json",
        'Content-Type': "application/json",
        'x-client-version': "3.6.0",
        'origin': "https://elements.envato.com",
        'referer': "https://elements.envato.com/",
        'accept-language': "en-US,en;q=0.9",
    }

    payload = {
        "language_code": "en",
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 204:
                return Result.available(url=show_url)

            if response.status_code == 422:
                data = response.json()
                error_msg = data.get("error_message", "").lower()

                if "already in use" in error_msg:
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_envato(email: str) -> Result:
    return await _check(email)
