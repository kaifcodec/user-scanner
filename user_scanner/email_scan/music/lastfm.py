import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.last.fm/join",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.last.fm",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            await client.get("https://www.last.fm/join", headers=headers)
            token = client.cookies.get("csrftoken")

            if not token:
                return Result.error("CSRF token not found")

            headers["X-CSRFToken"] = token
            payload = {
                "csrfmiddlewaretoken": token,
                "userName": "",
                "email": email,
                "password": "",
                "passwordConf": ""
            }

            response = await client.post(
                "https://www.last.fm/join/partial/validate",
                headers=headers,
                data=payload
            )

            if response.status_code != 200:
                return Result.error(f"HTTP {response.status_code}")

            data = response.json()
            email_info = data.get("email", {})

            if email_info.get("valid") is False and any("already registered" in str(msg).lower() for msg in email_info.get("error_messages", [])):
                return Result.taken()

            elif email_info.get("valid") is True:
                return Result.available()

            else:
                return Result.error(data)

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(e)


async def validate_lastfm(email: str) -> Result:
    return await _check(email)
