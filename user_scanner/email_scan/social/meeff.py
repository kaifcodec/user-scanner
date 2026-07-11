import httpx
import random
import string
from user_scanner.core.result import Result


def _generate_android_id() -> str:
    """Generate a random 16-character hex string representing an Android ID."""
    return "".join(random.choices(string.hexdigits.lower(), k=16))


async def _check(email: str) -> Result:
    url = "https://api.meeff.com/user/login/v4"
    show_url = "https://play.google.com/store/apps/details?id=com.noyesrun.meeff.kr"

    payload = {
        "provider": "email",
        "providerId": email,
        "providerToken": "",  # dummy password
        "os": "Android v11",
        "platform": "android",
        "device": "BRAND: VIVO, MODEL: VIVOY16, DEVICE: VIVOY16, PRODUCT: VIVOY16, DISPLAY: VIVOY!6_13_K.1098",
        "pushToken": "",
        "deviceUniqueId": _generate_android_id(),
        "deviceLanguage": "en",
        "deviceRegion": "US",
        "simRegion": "",
        "deviceGmtOffset": "+0530",
        "deviceRooted": 0,
        "deviceEmulator": 0,
        "appVersion": "7.1.2",
        "locale": "en"
    }

    headers = {
        'User-Agent': "okhttp/5.3.2",
        'Accept-Encoding': "gzip",
        'content-type': "application/json; charset=utf-8",
        'Cookie': "locale=en"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 401:
                data = response.json()
                error_msg = data.get("errorMessage", "")

                if "hasn't been signed up yet" in error_msg:
                    return Result.available(url=show_url)
                elif "passwords do not match" in error_msg:
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_meeff(email: str) -> Result:
    """
    Meeff email validator. Checks login endpoint. 
    """
    return await _check(email)
