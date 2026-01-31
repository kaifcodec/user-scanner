import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': '*/*',
        'Accept-Language': 'en,en-US;q=0.9',
        'Referer': 'https://www.eventbrite.com/signin/',
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.eventbrite.com',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            await client.get("https://www.eventbrite.com/signin/", headers=headers)

            csrf_token = client.cookies.get("csrftoken")
            if not csrf_token:
                return Result.error("CSRF token not found")

            headers["X-CSRFToken"] = csrf_token
            payload = {"email": email}

            response = await client.post(
                'https://www.eventbrite.com/api/v3/users/lookup/',
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("exists") is True:
                    return Result.taken()
                elif data.get("exists") is False:
                    return Result.available()
                else:
                    return Result.error(data)

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(e)


async def validate_eventbrite(email: str) -> Result:
    return await _check(email)
