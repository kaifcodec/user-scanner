import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://api.app.playtomic.io/v3/auth/methods"
    show_url = "https://playtomic.io/"

    headers = {
        'User-Agent': "Android 11",
        'Accept-Encoding': "gzip",
        'accept-language': "en",
        'content-type': "application/json",
        'x-requested-with': "com.playtomic.app 6.79.0"
    }

    params = {
        'email': email
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by Cloudflare/WAF (403)")
            if response.status_code == 429:
                return Result.error("Rate limited by Playtomic API (429)")
            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to parse JSON response payload")

            action_required = data.get("action_required")

            # Condition 1: action_required is False -> Account Exists
            if action_required is False:
                return Result.taken(url=show_url)

            # Condition 2: action_required is True -> Account Available
            if action_required is True:
                return Result.available(url=show_url)

            return Result.error("Unexpected boolean value for action_required key")

    except Exception as e:
        return Result.error(str(e))

async def validate_playtomic(email: str) -> Result:
    return await _check(email)
