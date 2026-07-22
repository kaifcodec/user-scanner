import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://faproulette.co"
    url = "https://faproulette.co/api/userCheckEmail"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": show_url,
        "Referer": show_url + "/",
    }
    payload = {"email": email, "timeoutID": 1}

    try:
        async with httpx.AsyncClient(http2=True, timeout=15.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited, wait for a few minutes")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()

            if data.get("success") == 1:
                return Result.available(url=show_url)

            error_msg = data.get("error", "")
            if "already in use" in error_msg:
                return Result.taken(url=show_url)

            return Result.error(error_msg or "Unexpected response body, report it via GitHub issues")

    except Exception as e:
        return Result.error(e)


async def validate_faproulette(email: str) -> Result:
    return await _check(email)
