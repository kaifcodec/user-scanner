import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://polarsteps.com"
    # Switching to the login endpoint to leverage 401 vs 404 status codes
    url = "https://www.polarsteps.com/api/login"

    payload = {
        "username": email,
        "password": "nic3_guys_finish_last"  # Dummy password for existence check
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'polarsteps-api-version': "69",
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': "?1",
        'Origin': "https://www.polarsteps.com",
        'Referer': "https://www.polarsteps.com/login",
        'Accept-Language': "en-US,en;q=0.9,ru;q=0.8",
        'Priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                content=json.dumps(payload),
                headers=headers
            )

            status = response.status_code

            # 401 means the account exists but the password (dummy) was wrong
            if status == 401:
                return Result.taken(url=show_url)

            # 404 means the username/email is not registered in their system
            if status == 404:
                return Result.available(url=show_url)

            if status == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if status == 429:
                return Result.error("Rate limited by Polarsteps (429)")

            return Result.error(f"Unexpected status code: {status}")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except Exception as e:
        return Result.error(e)


async def validate_polarsteps(email: str) -> Result:
    return await _check(email)
