import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    url = "https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri"
    params = {
        'key': "AIzaSyDv6JIzdDvbTBS-JWdR4Kl22UvgWGAyuo8"
    }
    headers = {
        'User-Agent': get_random_user_agent(),
        'Content-Type': "application/json",
        'x-client-version': "Chrome/JsCore/10.14.1/FirebaseCore-web",
        'origin': "https://www.justwatch.com",
        'referer': "https://www.justwatch.com/",
    }
    payload = {
        "identifier": email,
        "continueUri": "https://www.justwatch.com/"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                params=params,
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                registered = data.get("registered")

                if registered is True:
                    return Result.taken()
                elif registered is False:
                    return Result.available()

                return Result.error("Unexpected response body, report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_justwatch(email: str) -> Result:
    return await _check(email)
