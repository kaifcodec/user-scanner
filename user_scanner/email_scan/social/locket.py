import time
import uuid
import secrets
import httpx
from user_scanner.core.result import Result


def _generate_device_id() -> str:
    """Generate a random UUID v4 string with R suffix for amplitude device_id."""
    return f"{uuid.uuid4()}R"


def _generate_app_instance_id() -> str:
    """Generate a random 32-character hex string for Google Analytics app_instance_id."""
    return secrets.token_hex(16)


def _generate_timestamp() -> int:
    """Generate current epoch timestamp in milliseconds."""
    return int(time.time() * 1000)


async def _check(email: str) -> Result:
    url = "https://api.locketcamera.com/validateEmailAddress"
    show_url = "https://locketcamera.com"

    payload = {
        "data": {
            "analytics": {
                "amplitude": {
                    "device_id": _generate_device_id(),
                    "session_id": _generate_timestamp()
                },
                "experiments": {
                    "android_flag_2": 800,
                    "android_flag_1": 0,
                    "android_flag_9": 0,
                    "android_flag_8": 807,
                    "android_flag_7": 200,
                    "android_flag_6": 200,
                    "android_flag_5": 403,
                    "android_flag_4": 0,
                    "android_flag_10": 0,
                    "android_flag_3": 0
                },
                "google_analytics": {
                    "app_instance_id": _generate_app_instance_id()
                },
                "android_version": "1.234.2",
                "android_build": "577",
                "platform": "android"
            },
            "operation": "sign_in",
            "email": email
        }
    }

    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json; charset=utf-8"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                result_obj = data.get("result", {})
                status_val = result_obj.get("status")
                needs_reg = result_obj.get("needs_registration")
                err_msg = str(result_obj.get("error", ""))

                if needs_reg is False and status_val == 200:
                    return Result.taken(url=show_url)
                elif status_val == 601 or "does not exist" in err_msg:
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_locket(email: str) -> Result:
    """
    Locket Widget email validator. Checks validateEmailAddress endpoint.
    """
    return await _check(email)
