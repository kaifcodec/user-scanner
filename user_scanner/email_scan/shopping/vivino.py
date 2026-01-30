import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': 'application/json',
        'Referer': 'https://www.vivino.com/',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.get("https://www.vivino.com/", headers=headers)

            payload = {
                "email": email,
                "password": "password123"
            }

            response = await client.post(
                'https://www.vivino.com/api/login',
                headers=headers,
                json=payload
            )

            if response.status_code == 429:
                return Result.error("Rate limit exceeded")

            data = response.json()
            error_msg = data.get("error", "")

            if error_msg == "The supplied email does not exist":
                return Result.available()

            if not error_msg or "password" in error_msg.lower():
                return Result.taken()

            return Result.error(f"Vivino Error: {error_msg}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))

async def validate_vivino(email: str) -> Result:
    return await _check(email)
