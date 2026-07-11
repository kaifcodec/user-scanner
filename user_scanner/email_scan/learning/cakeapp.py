import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.cakeapp.me/gw/auth/email/validate"
    show_url = "https://play.google.com/store/apps/details?id=me.mycake"

    params = {
        'timezone': "330",
        'lang': "en",
        'languageToLearn': "en",
        'appVersion': "6.8.0",
        'os': "android",
        'osVersion': "11",
        'email': email
    }

    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Accept-Encoding': "gzip"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                result_status = data.get("result", "")

                if result_status == "SUCCESS":
                    inner_data = data.get("data", {})
                    has_error = inner_data.get("hasError")

                    if has_error is False:
                        return Result.available(url=show_url)
                    elif has_error is True and inner_data.get("errorType") == "DUPLICATED":
                        return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_cakeapp(email: str) -> Result:
    """
    Cake App email validator. Checks email validation endpoint without sending an email.
    """
    return await _check(email)
