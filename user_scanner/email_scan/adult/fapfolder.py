import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://fapfolder.club/includes/ajax/core/signup.php"
    show_url = "https://fapfolder.club"

    payload = {
        'username': "johnt5yt",
        'email': email,
        'email2': email,
        'password': "1",
        'field1': "",
        'privacy_agree': "on"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': "?1",
        'origin': "https://fapfolder.club",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://fapfolder.club/signup",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("403")

            data = response.json()
            message = data.get("message", "")

            if "belongs to an existing account" in message:
                return Result.taken(url=show_url)

            if "password must be at least" in message:
                return Result.available(url=show_url)

            return Result.error(f"Unexpected: {message[:50]}")

    except Exception as e:
        return Result.error(e)


async def validate_fapfolder(email: str) -> Result:
    return await _check(email)
