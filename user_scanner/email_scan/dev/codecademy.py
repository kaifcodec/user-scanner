import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.codecademy.com/register?redirect=%2F',
        'Content-Type': 'application/json',
        'Origin': 'https://www.codecademy.com',
    }

    try:
        async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
            init_res = await client.get("https://www.codecademy.com/register", headers=headers)

            csrf_match = re.search(
                r'name="csrf-token" content="([^"]+)"', init_res.text)
            if not csrf_match:
                return Result.error("Could not find CSRF token")

            headers["X-CSRF-Token"] = csrf_match.group(1)

            payload = {"user": {"email": email}}

            response = await client.post(
                'https://www.codecademy.com/register/validate',
                headers=headers,
                json=payload
            )

            if response.status_code == 400 and 'has already been taken' in response.text:
                return Result.taken()
            elif response.status_code == 200:
                return Result.available()

            return Result.error(f"Unexpected response: {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))


async def validate_codecademy(email: str) -> Result:
    return await _check(email)
