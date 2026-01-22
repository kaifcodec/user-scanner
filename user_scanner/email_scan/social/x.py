import httpx
from user_scanner.core.result import Result

async def _check(email):
    url = "https://api.x.com/i/users/email_available.json"
    params = {"email": email}
    headers = {
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "accept-encoding": "gzip, deflate, br, zstd",
        "sec-ch-ua-platform": "\"Android\"",
        "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "x-twitter-client-language": "en",
        "sec-ch-ua-mobile": "?1",
        "x-twitter-active-user": "yes",
        "origin": "https://x.com",
        "priority": "u=1, i"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes or use '-d' flag")

            data = response.json()
            taken_bool = data.get("taken")

            if taken_bool is True:
                return Result.taken()
            elif taken_bool is False:
                return Result.available()
            else:
                return Result.error("Unexpected error, report it via GitHub issues")

        except Exception as e:
            return Result.error(e)


async def validate_x(email: str) -> Result:
    return await _check(email)
