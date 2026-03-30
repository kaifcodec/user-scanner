import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://auth.nextdoor.com/v2/token"
    show_url = "https://nextdoor.com"

    payload = {
        'scope': "openid",
        'client_id': "NEXTDOOR-WEB",
        'login_type': "basic",
        'grant_type': "password",
        'username': email,
        'password': "vhj87uyguu77"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': "?1",
        'Origin': "https://nextdoor.com",
        'Referer': "https://nextdoor.com/",
        'Priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("403")

            data = response.json()
            error = data.get("error", "")

            if error == "invalid_grant":
                return Result.taken(url=show_url)

            if error == "not_found":
                return Result.available(url=show_url)

            return Result.error(f"Unexpected: {error}")

    except Exception as e:
        return Result.error(e)

async def validate_nextdoor(email: str) -> Result:
    return await _check(email)
