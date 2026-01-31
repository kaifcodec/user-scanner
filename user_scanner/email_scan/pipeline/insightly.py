import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    headers = {
        'authority': 'accounts.insightly.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'x-requested-with': 'XMLHttpRequest',
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://accounts.insightly.com',
        'referer': 'https://accounts.insightly.com/?plan=trial',
        'accept-language': 'en-US,en;q=0.9',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            payload = {'emailaddress': email}

            response = await client.post(
                'https://accounts.insightly.com/signup/isemailvalid',
                headers=headers,
                data=payload
            )

            if "An account exists for this address." in response.text:
                return Result.taken()

            elif response.text.strip() == "true":
                return Result.available()

            else:
                return Result.error(f"Unexpected response: {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))


async def validate_insightly(email: str) -> Result:
    return await _check(email)
