import httpx
import json
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    url = "https://jsso.indiatimes.com/sso/crossapp/identity/web/checkUserExists"

    payload = {
        "identifier": email
    }

    headers = {
        'User-Agent': get_random_user_agent(),
        'Content-Type': "application/json",
        'sdkversion': "0.8.1",
        'channel': "toi",
        'platform': "WAP",
        'Origin': "https://timesofindia.indiatimes.com",
        'Referer': "https://timesofindia.indiatimes.com/",
    }

    try:

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            response.raise_for_status()
            data = response.json()

            user_status = data.get("data", {}).get("status", "")

            if user_status == "VERIFIED_EMAIL":
                return Result.taken()

            elif user_status == "UNREGISTERED_EMAIL":
                return Result.available()
            elif user_status == "UNVERIFIED_EMAIL":
                return Result.taken("However email is not verified on the site")

            return Result.error("Unexpected response body, report it on github")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_indiatimes(email: str) -> Result:
    return await _check(email)
