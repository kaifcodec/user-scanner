import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.freelancer.com/api/users/0.1/users/check?compact=true&new_errors=true"
    show_url = "https://freelancer.com"

    payload = {
        "user": {
            "email": email
        }
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://www.freelancer.com',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 409 and "EMAIL_ALREADY_IN_USE" in response.text:
                return Result.taken(url=show_url)

            elif response.status_code == 200:
                return Result.available(url=show_url)

            return Result.error(f"Unexpected status code {response.status_code} or rate limit")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_freelancer(email: str) -> Result:
    return await _check(email)
