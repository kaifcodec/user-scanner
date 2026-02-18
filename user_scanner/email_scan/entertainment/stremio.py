import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    url = "https://api.strem.io/api/login"

    headers = {
        'User-Agent': get_random_user_agent(),
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
                    return Result.taken()
                elif error_data.get("wrongEmail") is True:
                    return Result.available()

                return Result.error("Unexpected response body, report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_stremio(email: str) -> Result:
    return await _check(email)
