import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://account.envato.com',
        'Referer': 'https://account.envato.com/sign_up',
    }

    payload = {'email': email}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                'https://account.envato.com/api/validate_email',
                headers=headers,
                data=payload
            )

            if 'Email is already in use' in response.text:
                return Result.taken()
            
            if response.status_code == 200:
                return Result.available()
            
            if "Page designed by Kotulsky" in response.text or response.status_code == 429:
                return Result.error("Rate limit or Cloudflare challenge detected")
            
            return Result.error(f"Unexpected response: {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))

async def validate_envato(email: str) -> Result:
    return await _check(email)
