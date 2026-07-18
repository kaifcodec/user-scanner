import httpx
import random
import string
from user_scanner.core.result import Result


def _generate_device_no() -> str:
    """Generate a random 33-character hex string representing a device number."""
    return "".join(random.choices("0123456789abcdef", k=33))


def _generate_ssid() -> str:
    """Generate a random 19-character numeric string representing an SSID."""
    return "".join(random.choices(string.digits, k=19))


async def _check(email: str) -> Result:
    url = "https://api.fantachat.ai/user/send/auth/code"
    show_url = "https://play.google.com/store/apps/details?id=com.api.fantachat"

    payload = {
        "email": email,
        "methodType": 2
    }

    device_no = _generate_device_no()
    ssid = _generate_ssid()

    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip",
        'x-system-region': "US",
        'sim-state': "EMPTY",
        'vpn-on': "true",
        'ssid': ssid,
        'device-model': "Pixel 6",
        'accept-language': "en",
        'x-app-name': "Fantasia",
        'timezone': "GMT+0",
        'source-platform': "Android",
        'app-version': "255",
        'app-version-code': "255",
        'device-no': device_no,
        'fingerprint': device_no,
        'authtoken': "",
        'content-type': "application/json; charset=UTF-8"
    }

    async with httpx.AsyncClient(timeout=20.0, http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=20.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                code = data.get("code")

                if code == "304" and data.get("message") == "User does not exist":
                    return Result.available(url=show_url)
                elif code == "0" and data.get("message") == "SUCCESS":
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_fantasia(email: str) -> Result:
    """
    Fantasia email validator. Note: This will send an auth code email if it exists.
    """
    return await _check(email)
