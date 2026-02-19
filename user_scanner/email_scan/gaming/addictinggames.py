import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://addictinggames.com"
    url = "https://prod.addictinggames.com/user/registerpass"

    params = {
        '_format': "json"
    }

    payload = {
        "name": [{"value": "tierd_knight"}],
        "mail": [{"value": email}],
        "pass": [{"value": "n0_0ne_asked_just_fight"}],
        "field_opt_in": [{"value": False}]
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Content-Type': "application/json",
        'Origin': "https://www.addictinggames.com",
        'Referer': "https://www.addictinggames.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(url, params=params, content=json.dumps(payload), headers=headers)
            body = response.text

            # Logic: If both 'tierd_knight' and 'email' are taken, the email exists.
            # If only 'tierd_knight' is mentioned as taken, the email is available.
            if response.status_code == 403:
                return Result.error("Cloudflare Bot Detection (403 Forbidden), try after sometime or use proxy")

            if "mail: The email address" in body and "is already taken" in body:
                return Result.taken(url=show_url)

            if "name: The username tierd_knight is already taken" in body:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body, report it on github")

    except Exception as e:
        return Result.error(e)


async def validate_addictinggames(email: str) -> Result:
    return await _check(email)
