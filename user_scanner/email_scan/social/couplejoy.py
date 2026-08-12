import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.couplejoyapp.com/v1/reset-password"
    show_url = "https://couplejoyapp.com"

    payload = {
        "email": email
    }

    headers = {
        "User-Agent": "okhttp/4.12.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json",
        "app-language": "en",
        "app-timezone": "UTC",
        "app-platform": "android",
        "app-version": "4.28.0",
        "app-locale": "en-US",
        "app-os-version": "11",
        "authorization": "Bearer null",
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                if data.get("success") is True:
                    return Result.taken(url=show_url)

            if response.status_code == 400:
                data = response.json()
                if data.get("code") == "EMAIL_NOT_FOUND":
                    return Result.available(url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_couplejoy(email: str) -> Result:
    """
    Couplejoy email validator. Checks reset-password endpoint.
    Loud module because it sends password reset email when account exists.
    """
    return await _check(email)
