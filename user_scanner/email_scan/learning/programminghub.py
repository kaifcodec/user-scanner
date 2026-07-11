import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api-prod.programminghub.io/v5/api/auth/recover/initiate"
    show_url = "https://play.google.com/store/apps/details?id=com.prghub.pro"

    payload = {
        "client": "android",
        "email": email
    }

    headers = {
        'User-Agent': "okhttp/5.3.2",
        'Accept-Encoding': "gzip",
        'client': "android",
        'locale': "en",
        'content-type': "application/json; charset=UTF-8"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 400:
                data = response.json()
                if data.get("status") is False and data.get("message") == "You are not registered with us":
                    return Result.available(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") is True and "user_id" in data.get("data", {}):
                    return Result.taken(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_programminghub(email: str) -> Result:
    """
    Programming Hub email validator. Note: This will send a recovery email if it exists.
    """
    return await _check(email)
