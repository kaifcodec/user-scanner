import httpx
import json
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent

async def _check(email: str) -> Result:
    url = "https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri"
    show_url = "https://crazygames.com"
    
    params = {
        'key': "AIzaSyAkBGn9sKEUBSMQ9CTFyHHxXas0tdcpts8"
    }

    payload = {
        "identifier": email,
        "continueUri": "https://www.crazygames.com/"
    }

    headers = {
        'User-Agent': get_random_user_agent(),
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
                return Result.taken(url=show_url)
            
            elif is_registered is False:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body, report it on github")

    except Exception as e:
        return Result.error(e)

async def validate_crazygames(email: str) -> Result:
    return await _check(email)
