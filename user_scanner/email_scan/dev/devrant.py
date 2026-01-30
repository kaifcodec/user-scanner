import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://devrant.com',
        'Referer': 'https://devrant.com/feed/top/month?login=1',
    }

    payload = {
        'app': '3',
        'type': '1',
        'email': email,
        'username': '',
        'password': '',
        'guid': '',
        'plat': '3',
        'sid': '',
        'seid': ''
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post('https://devrant.com/api/users', headers=headers, data=payload)

            if response.status_code != 200:
                return Result.error(f"Unexpected status code: {response.status_code}")

            data = response.json()
            error_msg = data.get('error', '')

            if error_msg == 'The email specified is already registered to an account.':
                return Result.taken()

            return Result.available()

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))


async def validate_devrant(email: str) -> Result:
    return await _check(email)
