import httpx
import json
import time
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    url = "https://www.pinterest.com/resource/ApiResource/get/"

    data_str = json.dumps({
        "options": {
            "url": "/v3/register/exists/",
            "data": {"email": email}
        },
        "context": {}
    }, separators=(',', ':'))

    params = {
        'source_url': "/signup/step1/",
        'data': data_str,
        '_': str(int(time.time() * 1000))
    }

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "application/json, text/javascript, */*, q=0.01",
        'Accept-Language': "en-US,en;q=0.9",
        'x-pinterest-pws-handler': "www/signup/[step].js",
        'x-app-version': "2503cde",
        'x-requested-with': "XMLHttpRequest",
        'x-pinterest-source-url': "/signup/step1/",
        'x-pinterest-appstate': "active",
        'origin': "https://www.pinterest.com",
        'referer': "https://www.pinterest.com/",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'priority': "u=1, i"
    }

    try:

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 200:
                resp_json = response.json()
                resource_response = resp_json.get("resource_response", {})

                exists = resource_response.get("data")

                if exists is True:
                    return Result.taken()
                elif exists is False:
                    return Result.available()

                return Result.error("Unexpected response body, report it via GitHub issues")

            if response.status_code == 403:
                return Result.error("Access Forbidden (403) - Potential IP Block")

            if response.status_code == 429:
                return Result.error("Rate limited (429)")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_pinterest(email: str) -> Result:
    return await _check(email)
