import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.femometer.com/v1/user_location"
    show_url = "https://www.femometer.com"

    params = {
        'country_code': "0",
        'phone_no': "0",
        'email': email,
        'app_flag': "1",
        'language': "2",
        'localTimezone': "UTC",
        'app_version': "5.43.5(4260)",
        'platform_type': "1",
        'isGooglePlay': "true"
    }

    headers = {
        'Host': "api-us.femometer.com",
        'User-Agent': "okhttp/4.12.0",
        'Accept-Encoding': "gzip",
        'content-type': "application/json; charset=utf-8"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                user_id = data.get("userId")
                location = data.get("userLocation")

                if user_id == 0 and location == 0:
                    return Result.available(url=show_url)
                elif user_id and user_id != 0:
                    extras = {}
                    extras["user id"] = user_id
                    if data.get("url"):
                        extras["server location"] = data.get("url")

                    return Result.taken(url=show_url, extra=extras)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_femometer(email: str) -> Result:
    """
    Femometer email validator. Checks user location endpoint for account existence.
    """
    return await _check(email)
