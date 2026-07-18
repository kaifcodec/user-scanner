import httpx
import json
import secrets
from user_scanner.core.result import Result


def _generate_android_id() -> str:
    return secrets.token_hex(8)


async def _check(email: str) -> Result:
    url = "https://api.getslowly.com/auth/email/passcode"
    show_url = "https://getslowly.com"

    android_id = _generate_android_id()
    device_info = {
        "platform": "android",
        "bundleId": "com.slowlyapp",
        "device": "Pixel6",
        "deviceType": "Handset",
        "brand": "Google",
        "system": "13",
        "res": "1080x2400",
        "ui_language": "en",
        "deviceLocales": [{"isRTL": False, "languageTag": "en-US", "countryCode": "US", "languageCode": "en"}],
        "currency": ["USD"],
        "timezone": "America/New_York",
        "jb": False,
        "hook": False,
        "adb": False,
        "canMock": False,
        "externalStorage": False,
        "uuid": android_id,
        "carrier": "",
        "serial": "unknown",
        "locationEnabled": False,
        "isEmulator": False,
        "fontScale": 1,
        "pushPermission": "granted",
        "networkType": "wifi",
        "networkDetails": {
            "isConnectionExpensive": False,
            "txLinkSpeed": 866,
            "rxLinkSpeed": -1,
            "linkSpeed": 866,
            "subnet": "255.255.255.0",
            "ipAddress": "192.168.1.15",
            "frequency": 5805,
            "strength": 99,
            "bssid": "00:11:22:33:44:55"
        },
        "rc_currency": "USD",
        "rc_offerings": "plus_699_intro",
        "version": "9.5.2"
    }

    payload = {
        "email": email,
        "device": json.dumps(device_info),
        "checkpass": True
    }

    headers = {
        'User-Agent': "okhttp/4.11.0",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json"
    }

    async with httpx.AsyncClient(timeout=15.0, http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 400:
                data = response.json()
                if data.get("error") == "email_not_found":
                    return Result.available(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") in ["email_sent", "email_already_sent"]:
                    return Result.taken(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_slowly(email: str) -> Result:
    """
    Slowly email validator. Note: This will send an email passcode to the target if the email exists.
    """
    return await _check(email)
