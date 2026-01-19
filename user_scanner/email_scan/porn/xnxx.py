import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://www.xnxx.com/account/checkemail"
    params = {'email': email}
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'X-Requested-With': "XMLHttpRequest",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': "?1",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://www.xnxx.com/",
        'Accept-Language': "en-US,en;q=0.9"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")
            
            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()
            is_taken = data.get("result") is False and data.get("code") == 1

            if is_taken:
                return Result.taken()
            else:
                return Result.available()

        except Exception as e:
            return Result.error(e)

async def validate_xnxx(email: str) -> Result:
    return await _check(email)
