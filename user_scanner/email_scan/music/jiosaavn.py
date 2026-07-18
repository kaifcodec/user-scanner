import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.saavn.com/api.php"
    show_url = "https://www.jiosaavn.com"

    payload = {
        'cc': "",
        'dolby_support': "false",
        'r_device': "true",
        'r_device_flow': "ir:,su,idr,",
        'app_version': "10.7.1",
        '_marker': "0",
        'ctx': "android",
        'tz': "UTC",
        'api_version': "4",
        'manufacturer': "Google",
        'provider_state': "checking",
        'readable_version': "10.7.1",
        'build': "TP1A.220624.021",
        'v': "548",
        '_format': "json",
        'is_jio_user': "false",
        'model': "Pixel 6",
        '__call': "user.isRegisteredEmail",
        'network_subtype': "",
        'state': "logout",
        'network_type': "WIFI",
        'email': email
    }

    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TP1A.220624.021)",
        'Accept-Encoding': "gzip"
    }

    async with httpx.AsyncClient(timeout=20.0, http2=True) as client:
        try:
            # Form-encoded POST request
            response = await client.post(url, data=payload, headers=headers, timeout=20.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")

                if status is False:
                    return Result.available(url=show_url)
                elif status is True:
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_jiosaavn(email: str) -> Result:
    """
    JioSaavn email validator. Checks if email is registered.
    """
    return await _check(email)
