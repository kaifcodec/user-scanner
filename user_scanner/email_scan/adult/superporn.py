import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent

async def _check(email: str) -> Result:
    show_url = "https://superporn.com"
    url = "https://api.superporn.com/signup/check-email"
    
    payload = {
        'lang': "en_US",
        'email': email
    }

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Origin': "https://www.superporn.com",
        'Referer': "https://www.superporn.com/signup",
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.post(url, data=payload, headers=headers)
            data = response.json()

            is_error = data.get("error")
            
            if is_error is True:
                if "Email is in use" in data.get("message", ""):
                    return Result.taken(url=show_url)
            
            elif is_error is False:
                if data.get("result") == "ok":
                    return Result.available(url=show_url)

            return Result.error("Unexpected response body, report it via GitHub issues")

    except Exception as e:
        return Result.error(e)

async def validate_superporn(email: str) -> Result:
    return await _check(email)
