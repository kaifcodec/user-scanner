import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://registerdisney.go.com/jgc/v8/client/ESPN-ONESITE.WEB-PROD/guest-flow"
    params = {
        'langPref': "en",
        'feature': "no-password-reuse"
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Content-Type': "application/json",
        'origin': "https://cdn.registerdisney.go.com",
        'referer': "https://cdn.registerdisney.go.com/",
        'accept-language': "en-US,en;q=0.9",
    }
    payload = {"email": email}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                params=params,
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                flow = data.get("guestFlow")

                if flow == "LOGIN_FLOW":
                    return Result.taken()
                elif flow == "REGISTRATION_FLOW":
                    return Result.available()

                return Result.error("Unexpected response body, report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_espn(email: str) -> Result:
    return await _check(email)
