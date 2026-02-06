import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://made.porn/endpoint/api/json/change-password"

    payload = {
        'email': email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Origin': "https://made.porn",
        'Referer': "https://made.porn/login",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, data=payload, headers=headers)
            data = response.json()

            if "sent an email with a link" in data.get("Text", ""):
                return Result.taken()

            if "The email address is incorrect" in data.get("Error", ""):
                return Result.available()

            return Result.error("Unexpected response body, report it on github")

    except Exception as e:
        return Result.error(e)

async def validate_made_porn(email: str) -> Result:
    return await _check(email)
