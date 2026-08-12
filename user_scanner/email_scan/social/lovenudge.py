import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.lovenudgeapp.com/api/register/check"
    show_url = "https://lovenudgeapp.com"

    params = {
        "email": email,
        "time_zone": "UTC",
        "app_version": "5.2.10",
    }

    headers = {
        "User-Agent": "okhttp/4.11.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    if data["data"] is True:
                        return Result.taken(url=show_url)
                    elif data["data"] is False:
                        return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_lovenudge(email: str) -> Result:
    """
    Love Nudge email validator. Checks register/check endpoint.
    """
    return await _check(email)
