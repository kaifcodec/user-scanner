import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.xvideos.com/account/checkemail"
    params = {'email': email}

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Encoding': "identity",
        'X-Requested-With': "XMLHttpRequest",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua': "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        'sec-ch-ua-mobile': "?1",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://www.xvideos.com/",
        'Accept-Language': "en-US,en;q=0.9"
    }

    async with httpx.AsyncClient(http2=True, timeout=3) as client:
        try:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited, wait for a few minutes")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()

            exists_bool = data.get("result")

            if exists_bool is True:
                return Result.available()
            elif exists_bool is False:
                return Result.taken()
            else:
                return Result.error("Unexpected error, report it via GitHub issues")

        except Exception as e:
            return Result.error(e)


async def validate_xvideos(email: str) -> Result:
    return await _check(email)
