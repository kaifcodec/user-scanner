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
        "sec-fetch-site": "same-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://x.com/",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=1, i"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            data = response.json()
            taken_bool= data["taken"]
            if taken_bool is True:
                return Result.taken()

            elif taken_bool is False:
                return Result.available()
        except Exception as e:
            return Result.error(e)

def validate_x(email: str) -> Result:
    return _check(email)
