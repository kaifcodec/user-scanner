import httpx
import json
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    url = "https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri"

    params = {
        'key': "AIzaSyDWz9TZvPscN7qFdG6z1bvLh98eXVBSUPM"
    }

    payload = {
        "identifier": email,
        "continueUri": "https://www.aljazeera.com/account/sign-up"
    }

    headers = {
        'User-Agent': get_random_user_agent(),
        'Content-Type': "application/json",
        'Origin': "https://www.aljazeera.com",
        'Referer': "https://www.aljazeera.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, params=params, content=json.dumps(payload), headers=headers)
            data = response.json()

            is_registered = data.get("registered")

            if is_registered is True:
                return Result.taken()

            if is_registered is False:
                return Result.available()

            return Result.error("Unexpected response body, report it on github")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out while reaching Al Jazeera Auth")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_aljazeera(email: str) -> Result:
    return await _check(email)
