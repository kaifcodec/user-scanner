import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://auth.services.adobe.com/signin/v2/users/accounts"

    payload = {
        "username": email,
        "usernameType": "EMAIL"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Content-Type': "application/json",
        'x-ims-clientid': "BehanceWebSusi1",
        'Origin': "https://auth.services.adobe.com",
        'Referer': "https://www.behance.net/",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                return Result.error("Unexpected response body, report it on github")

            if not data:
                return Result.available()

            for account in data:
                methods = account.get("authenticationMethods", [])
                if any(m.get("id") == "password" for m in methods):
                    return Result.taken()

            return Result.available()

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_adobe(email: str) -> Result:
    return await _check(email)
