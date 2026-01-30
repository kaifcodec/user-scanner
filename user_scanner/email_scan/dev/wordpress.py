import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = f"https://public-api.wordpress.com/rest/v1.1/users/{email}/auth-options"

    params = {
        'http_envelope': "1"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': "application/json",
        'sec-ch-ua-platform': '"Linux"',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        'sec-ch-ua-mobile': "?0",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://public-api.wordpress.com/wp-admin/rest-proxy/?v=2.0",
        'accept-language': "en-US,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code != 200:
                return Result.error(f"WordPress API returned status {response.status_code}")

            data = response.json()

            inner_code = data.get("code")
            body = data.get("body", {})

            if inner_code == 200:
                return Result.taken()
            elif inner_code == 404 and body.get("error") == "unknown_user":
                return Result.available()
            else:
                error_msg = body.get("message", "Unknown API response")
                return Result.error(f"WordPress Error: {error_msg}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))


async def validate_wordpress(email: str) -> Result:
    return await _check(email)
