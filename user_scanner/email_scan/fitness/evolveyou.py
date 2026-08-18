import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://fitness.evolveyouapi.com/api/v1/auth"
    show_url = "https://evolveyou.app"

    payload = {
        "username": email,
        "password": "dummy_password_xyz123",
    }

    headers = {
        "User-Agent": "okhttp/4.12.0",
        "Accept": "application/json; text/plain; charset=utf-8",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json",
        "x-device-type": "unknown",
        "x-consumer": "Tablet",
        "x-app-version": "9.7.7",
        "x-timezone-offset": "-480",
        "os": "android",
        "accept-language": "en-gb",
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code in (400, 401):
                data = response.json()
                msg = str(data.get("message", "")).lower()

                if "incorrect username or password" in msg:
                    return Result.taken(url=show_url)

                if "user not found" in msg:
                    return Result.available(url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_evolveyou(email: str) -> Result:
    """
    EvolveYou fitness app email validator.
    Checks auth endpoint with a dummy password.
    """
    return await _check(email)
