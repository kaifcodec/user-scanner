import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://mixcloud.com"
    refresh_url = "https://app.mixcloud.com/csrf/refresh/"
    register_url = "https://app.mixcloud.com/authentication/email-register/"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'x-requested-with': "XMLHttpRequest",
        'x-mixcloud-platform': "www",
        'origin': "https://www.mixcloud.com",
        'referer': "https://www.mixcloud.com/",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            await client.get(refresh_url, headers=headers)

            csrf = client.cookies.get("csrftoken")
            if not csrf:
                return Result.error("Failed to extract csrftoken from refresh endpoint")

            headers['x-csrftoken'] = csrf

            payload = {
                'email': email,
                'username': "scanner_user_99",
                'password': "",
                'ch': 'y'
            }

            response = await client.post(register_url, data=payload, headers=headers)
            status = response.status_code

            if status == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if status == 200:
                data = response.json()
                errors = data.get("data", {}).get("$errors", {})

                email_errors = errors.get("email", [])
                if any("already in use" in err for err in email_errors):
                    return Result.taken(url=show_url)

                return Result.available(url=show_url)

            if status == 429:
                return Result.error("Rate limited by Mixcloud")

            return Result.error(f"Unexpected status code: {status}")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except Exception as e:
        return Result.error(e)


async def validate_mixcloud(email: str) -> Result:
    return await _check(email)
