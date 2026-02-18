import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent

async def _check(email: str) -> Result:
    url = "https://www.codewars.com/join"

    params = {'language': 'javascript'}

    payload = {
        'utf8': "✓",
        '_method': "patch",
        'user[email]': email,
        'user[username]': "",
        'user[password]': "",
        'user[password_confirmation]': "",
        'utm[source]': "",
        'utm[medium]': "",
        'utm[campaign]': "",
        'utm[term]': "",
        'utm[content]': "",
        'utm[referrer]': "https://www.google.com/"
    }

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Origin': "https://www.codewars.com",
        'Referer': "https://www.codewars.com/join",
        'Upgrade-Insecure-Requests': "1",
    }

    try:
        async with httpx.AsyncClient(timeout=7.0, follow_redirects=True) as client:
            response = await client.post(url, params=params, data=payload, headers=headers)
            html = response.text

            if "is already taken" in html:
                return Result.taken()

            if "can&#39;t be blank" in html:
                return Result.available()

            return Result.error("Unexpected response pattern")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")

async def validate_codewars(email: str) -> Result:
    return await _check(email)
