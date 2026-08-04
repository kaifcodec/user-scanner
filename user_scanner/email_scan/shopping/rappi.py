import sys
import time
import secrets
import httpx
from user_scanner.core.result import Result


def _generate_device_id() -> str:
    """Generate a random 16-character hex string for deviceid."""
    return secrets.token_hex(8)


def _generate_timestamp() -> str:
    """Generate current epoch timestamp in milliseconds."""
    return str(int(time.time() * 1000))


async def _check(email: str) -> Result:
    url_check = "https://services.rappi.com.ar/api/rocket/user/account/check-email"
    url_login = "https://services.rappi.com.ar/api/rocket/login/email/application_user"
    show_url = "https://www.rappi.com"

    device_id = _generate_device_id()
    ts = _generate_timestamp()

    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TP1A.220624.021)",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'user_id': "",
        'custom_country_code': "AR",
        'deviceid': device_id,
        'app-version': "88721",
        'app-version-name': "8.35.20260724-88721",
        'store-platform': "google",
        'amplitude-session-id': ts,
        'timestamp': ts,
        'request_timestamp': ts,
        'accept-language': "en-US",
        'language': "en",
        'country-code': "AR",
        'fp_dp_id': "3703578013",
        'content-type': "application/json; charset=UTF-8"
    }

    payload_check = {
        "email": email
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            # Silent check-email endpoint
            response = await client.post(url_check, json=payload_check, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited, wait 30 to 60s and retry", url=show_url)

            if response.status_code == 200:
                data = response.json()
                exists = data.get("exists")

                if exists is True:
                    # Explicitly verified email exists
                    pass
                elif exists is False:
                    return Result.available(url=show_url)
                else:
                    return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            else:
                return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

            # If registered (exists is True), check if --allow-loud was passed
            allow_loud = "--allow-loud" in sys.argv

            if not allow_loud:
                # Return TAKEN silently without hitting the loud login endpoint
                return Result.taken(reason="Use flag '--allow-loud' to see the target's masked phone number", url=show_url)

            # If --allow-loud is passed, proceed to Endpoint 2 to extract masked phone info
            payload_login = {
                "email": email,
                "scope": "all"
            }
            new_ts = _generate_timestamp()
            headers['timestamp'] = new_ts
            headers['request_timestamp'] = new_ts

            response_login = await client.post(url_login, json=payload_login, headers=headers, timeout=6.0)

            extras = {}
            if response_login.status_code in [200, 400, 401, 422]:
                try:
                    data_login = response_login.json()
                    err = data_login.get("error", {})
                    if isinstance(err, dict):
                        phone = err.get("verification_value")
                        if phone:
                            extras["phone"] = phone
                        v_type = err.get("verification_type")
                        if v_type:
                            extras["verification_type"] = v_type
                except Exception:
                    pass

            return Result.taken(url=show_url, extra=extras)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_rappi(email: str) -> Result:
    """
    Rappi email validator.
    Silent by default (hits check-email endpoint).
    When --allow-loud is passed, also hits the login endpoint to extract masked phone intelligence.
    """
    return await _check(email)
