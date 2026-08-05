import time
import secrets
import httpx
from user_scanner.core.result import Result


def _generate_device_id() -> str:
    """Generate a random 16-character hex string for device ID."""
    return secrets.token_hex(8)


def _generate_timestamp() -> str:
    """Generate current epoch timestamp in milliseconds."""
    return str(int(time.time() * 1000))


def _generate_random_param() -> str:
    """Generate a random 12-digit string for the 'random' parameter."""
    return str(secrets.randbelow(900000000000) + 100000000000)


async def _check(email: str) -> Result:
    url = "https://account.glowing.com/a/v3/users/signup_email"
    show_url = "https://glowing.com"

    params = {
        'fc': "1",
        'random': _generate_random_param(),
        'android_version': "11.22.1",
        'unit': "imperial"
    }

    payload = {
        'email': email
    }

    device_id = _generate_device_id()
    ts = _generate_timestamp()

    headers = {
        'Host': "glow.glowing.com",
        'User-Agent': "okhttp/4.9.3",
        'Accept-Encoding': "gzip",
        'app-version': "11.22.1",
        'build-number': "112201",
        'bundle-id': "com.glow.android",
        'client-platform': "android",
        'device-id': device_id,
        'device-model': "Google Pixel 6",
        'glowoccurtime': ts,
        'language': "en",
        'platform': "android",
        'platform-version': "33",
        'rn-version': "5.0.3",
        'time-zone': "UTC",
        'x-app-code-name': "emma",
        'x-app-device-id': device_id,
        'x-app-locale': "en_US",
        'x-app-timezone': "UTC",
        'x-app-version-code': "112201",
        'x-platform': "Android",
        'x-sub-app': "glow",
        'x-sub-app-version': "11.22.1"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            # Note: User's example used data=payload, which means form-encoded POST
            response = await client.post(url, params=params, data=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                valid = data.get("data", {}).get("valid")
                msg = str(data.get("msg", ""))

                if valid == 1:
                    return Result.available(url=show_url)
                elif valid == 0 or "already been taken" in msg:
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_glow(email: str) -> Result:
    """
    Glow / Emma email validator. Checks signup_email endpoint.
    """
    return await _check(email)
