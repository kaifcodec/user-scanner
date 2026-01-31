import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    headers = {
        'authority': 'api.hubspot.com',
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'content-type': 'application/json',
        'origin': 'https://app.hubspot.com',
        'referer': 'https://app.hubspot.com/',
        'accept-language': 'en-US,en;q=0.9',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            payload = {
                "email": email,
                "password": "",
                "rememberLogin": False
            }

            response = await client.post(
                'https://api.hubspot.com/login-api/v1/login',
                headers=headers,
                json=payload
            )

            # HubSpot returns 400 for both "wrong password" and "user not found"
            if response.status_code == 400:
                data = response.json()
                status = data.get("status")

                if status == "INVALID_PASSWORD":
                    return Result.taken()

                elif status == "INVALID_USER":
                    return Result.available()

                else:
                    return Result.error(data)

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))


async def validate_hubspot(email: str) -> Result:
    return await _check(email)
