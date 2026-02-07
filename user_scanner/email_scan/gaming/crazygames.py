import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri"
    
    params = {
        'key': "AIzaSyAkBGn9sKEUBSMQ9CTFyHHxXas0tdcpts8"
    }

    payload = {
        "identifier": email,
        "continueUri": "https://www.crazygames.com/"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'origin': "https://www.crazygames.com",
        'referer': "https://www.crazygames.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, params=params, content=json.dumps(payload), headers=headers)
            data = response.json()

            is_registered = data.get("registered")

            if is_registered is True:
                return Result.taken()
            
            elif is_registered is False:
                return Result.available()

            return Result.error("Unexpected response body, report it on github")

    except Exception as e:
        return Result.error(e)

async def validate_crazygames(email: str) -> Result:
    return await _check(email)
