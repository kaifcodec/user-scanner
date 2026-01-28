import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://replit.com/data/user/exists"
    
    payload = {
        "email": email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua': "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
        'sec-ch-ua-mobile': "?1",
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://replit.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://replit.com/signup",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    async with httpx.AsyncClient(http2=False, timeout=5.0) as client:
        try:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 403:
                return Result.error("403 Forbidden")

            data = response.json()
            exists = data.get("exists")

            if exists is True:
                return Result.taken()
            if exists is False:
                return Result.available()

            return Result.error("Unexpected response format")

        except Exception as e:
            return Result.error(str(e))

async def validate_replit(email: str) -> Result:
    return await _check(email)
