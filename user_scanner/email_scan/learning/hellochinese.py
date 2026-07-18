import httpx
import json
import random
from datetime import datetime
from user_scanner.core.result import Result


def _generate_device_id() -> str:
    """Generate a random 32-character hex string representing a device ID."""
    return "".join(random.choices("0123456789abcdef", k=32))


def _get_time_str() -> str:
    """Generate the timestamp in the required format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +0530")


async def _check(email: str) -> Result:
    url = "http://api3.hellochinese.cc/v1/passport/forget_password"
    show_url = "https://play.google.com/store/apps/details?id=com.hellochinese"

    payload = {
        'email': email
    }

    env_data = {
        "appVer": "7.10.35",
        "cid": None,
        "device": "Pixel 6",
        "deviceId": _generate_device_id(),
        "lang": "en",
        "locale": "en-US",
        "network": "wifi",
        "osVer": "13",
        "platform": "android",
        "time": _get_time_str()
    }

    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TP1A.220624.021)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Env': json.dumps(env_data)
    }

    async with httpx.AsyncClient(timeout=15.0, http2=False) as client:
        try:
            # Form-encoded POST request
            response = await client.post(url, data=payload, headers=headers, timeout=15.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                code = data.get("code")

                if code == 103:
                    return Result.available(url=show_url)
                elif code == 0:
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_hellochinese(email: str) -> Result:
    """
    HelloChinese email validator. Note: This will send a password reset email if it exists.
    """
    return await _check(email)
