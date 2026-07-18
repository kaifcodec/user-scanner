import httpx
import random
import string
from user_scanner.core.result import Result


def _generate_device_id() -> str:
    """Generate a random 16-character hex string for device ID."""
    return "".join(random.choices(string.hexdigits.lower(), k=16))


async def _check(email: str) -> Result:
    url = "https://prod-api.hoichoi.dev/core/api/v1/auth/signinup/code"
    show_url = "https://www.hoichoi.tv"

    device_id = _generate_device_id()

    params = {
        'platform': "ANDROID_MOBILE",
        'language': "english",
        'appVersion': "3.1.44",
        'deviceId': device_id
    }

    payload = {
        "email": email,
        "deviceId": device_id
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 13; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "gzip;q=1.0,deflate;q=0.9",
        'Content-Type': "application/json",
        'x-hoichoi-siteid': "hoichoitv",
        'x-bypass-proxy': "true"
    }

    async with httpx.AsyncClient(timeout=15.0, http2=True) as client:
        try:
            response = await client.post(url, params=params, json=payload, headers=headers, timeout=15.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 400:
                data = response.json()
                if data.get("errorCode") == "EMAIL_SIGNUP_NOT_SUPPORTED":
                    return Result.available(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK" and data.get("flowType") == "USER_INPUT_CODE":
                    return Result.taken(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_hoichoi(email: str) -> Result:
    """
    Hoichoi email validator. Note: This will send a sign-in OTP email if it exists.
    """
    return await _check(email)
