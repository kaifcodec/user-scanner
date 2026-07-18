import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://fbprod.flipboard.com/v1/flipboard/checkEmail/0"
    show_url = "https://flipboard.com"

    params = {
        'email': email,
        'ver': "4.3.56.5508",
        'device': "aphone-google-pixel-30",
        'locale': "en_US",
        'lang': "en",
        'locale_cg': "en_US",
        'screensize': "6.0",
        'app': "flipboard",
        'udid': "8610cbecde6c89b6b0cb5449f2cd9f13d1cba8f4",
        'tuuid': "52987290-d242-48a8-b10c-7b87fd8c7424"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 13; Pixel 6 Build/TP1A.220624.021; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/149.0.7827.163 Mobile Safari/537.36 Flipboard/4.3.56/5508,4.3.56.5508",
        'Accept-Encoding': "gzip"
    }

    async with httpx.AsyncClient(timeout=15.0, http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=15.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            data = response.json()

            if data.get("success") is True:
                if data.get("valid") is False:
                    return Result.taken(url=show_url)
                elif data.get("valid") is True:
                    return Result.available(url=show_url)

            return Result.error("Unexpected JSON response from Flipboard, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(str(e), url=show_url)


async def validate_flipboard(email: str) -> Result:
    """
    Flipboard email validator.
    """
    return await _check(email)
