import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.hanzii.net/api/password/reset"
    show_url = "https://play.google.com/store/apps/details?id=com.eup.hanzii"

    payload = {
        "X-localization": "en",
        "email": email
    }

    headers = {
        'User-Agent': "com.eup.hanzii/768 (Linux; U; Android 13; en_US; Pixel 6; Build/TP1A.220624.021; Cronet/149.0.7827.102)",
        'Accept-Encoding': "gzip, deflate",
        'content-type': "application/json; charset=UTF-8",
        'priority': "u=1, i"
    }

    async with httpx.AsyncClient(timeout=15.0, http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 401:
                data = response.json()
                if data.get("error") == "Email is not exist" and data.get("code") == 401:
                    return Result.available(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "Success":
                    return Result.taken(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_hanzii(email: str) -> Result:
    """
    Hanzii email validator. Note: This will send a password reset email if it exists.
    """
    return await _check(email)
