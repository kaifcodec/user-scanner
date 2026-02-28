import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://nebula.tv/auth/registration/"
    show_url = "https://nebula.tv"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'nebula-app-version': "26.3.0",
        'nebula-platform': "web",
        'Origin': "https://nebula.tv",
        'Referer': "https://nebula.tv/join",
        'Priority': "u=1, i"
    }

    payload = {
        "email": email,
        "password": "5",
        "agreed_to_terms": True,
        "opt_in_to_communications": False
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if response.status_code == 429:
                return Result.error("Rate limited by Nebula (429)")

            # Nebula returns 400 Bad Request when validation fails, which is expected here
            data = response.json()

            if "email" in data:
                email_errors = data.get("email", [])
                if any("already registered" in err for err in email_errors):
                    return Result.taken(url=show_url)

            if "password" in data and "email" not in data:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_nebula_tv(email: str) -> Result:
    return await _check(email)
