import httpx
import random
from datetime import datetime, timezone
from user_scanner.core.result import Result


def _generate_udid() -> str:
    """Generate a 32-character uppercase hex string."""
    return "".join(random.choices("0123456789ABCDEF", k=32))


def _get_amz_date() -> str:
    """Generate the x-amz-date timestamp."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


async def _check(email: str) -> Result:
    url = "https://api.babbel.io/gamma/v2/en/users/"
    show_url = "https://play.google.com/store/apps/details?id=com.babbel.mobile.android.en"

    payload = {
        "user": {
            "email": email,
            "locale": "",
            "learn_language_alpha3": "QMS",
            "registration_date": "",
            "uuid": "",
            "authentication_token": "",
            "country_alpha3": "",
            "email_validated": False,
            "privacy_policy": False,
            "terms_and_conditions": False,
            "password": "",
            "firstname": "nopi",
            "signin_token": "",
            "captcha": {}
        }
    }

    headers = {
        'User-Agent': "Babbel/22.4.0 (Android 30.0; Google Pixel 6; Google; Google; en_US)",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'x-device-udid': _generate_udid(),
        'x-amz-date': _get_amz_date(),
        'content-type': "application/json; charset=UTF-8"
    }

    async with httpx.AsyncClient(timeout=15.0, http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 422:
                data = response.json()
                messages = data.get("error", {}).get("messages", [])

                for msg in messages:
                    if msg.get("attribute") == "email" and "taken" in msg.get("details", []):
                        return Result.taken(url=show_url)

                # If we didn't find the email taken error, it's available
                return Result.available(url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_babbel(email: str) -> Result:
    """
    Babbel email validator. Checks registration endpoint without sending an email.
    """
    return await _check(email)
