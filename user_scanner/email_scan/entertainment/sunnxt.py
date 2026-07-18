import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.sunnxt.com/user/v2/userAccountStatus/"
    show_url = "https://www.sunnxt.com"

    params = {
        'userid': email,
        'partner_id': "",
        'source': ""
    }

    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TP1A.220624.021)",
        'Accept-Encoding': "gzip",
        'clientkey': "1bd3195692e434d1ad72ad4db17e7b00841d6ef0f16616cfe33d8bb2e5a719e3",
        'accept-language': "en",
        'contentlanguage': "english",
        'x-myplex-platform': "android",
        'appversion': "200380",
        'x-myplex-maturity-level': "",
        'x-ucv': "5"
    }

    async with httpx.AsyncClient(timeout=20.0, http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=20.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")

                if status == "SUCCESS":
                    user_available = data.get("user_available")
                    if user_available is False:
                        return Result.available(url=show_url)
                    elif user_available is True:
                        extras = {}
                        
                        subscription_status = data.get("subscription_status")
                        if subscription_status is not None:
                            extras["subscription status"] = subscription_status
                            
                        partner_id = data.get("partner_id")
                        if partner_id is not None:
                            extras["partner id"] = partner_id

                        password_available = data.get("password_available")
                        if password_available is not None:
                            extras["password available"] = password_available

                        login_account_type = data.get("login_account_type")
                        if login_account_type is not None:
                            extras["account type"] = login_account_type

                        return Result.taken(url=show_url, extra=extras)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_sunnxt(email: str) -> Result:
    """
    Sun NXT email validator. Checks if the email registered and returns account attributes.
    """
    return await _check(email)
