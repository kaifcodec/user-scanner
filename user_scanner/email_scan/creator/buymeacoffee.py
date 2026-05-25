import httpx
import secrets
import string
from user_scanner.core.result import Result

def _generate_fingerprint(length: int = 20) -> str:
    """Generates a random alphanumeric device fingerprint matching the structural footprint."""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

async def _check(email: str) -> Result:
    url = "https://app.buymeacoffee.com/api/v1/email/login"
    show_url = "https://www.buymeacoffee.com/"

    # Preserving the native Android application headers and injecting a randomized fingerprint
    headers = {
        'User-Agent': "BuyMeaCoffee-Android-1.4.90",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'x-device-fingerprint': _generate_fingerprint()
    }

    payload = {
        "email": email,
        "client_response": "",
        "captcha_version": "v3"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by Cloudflare/WAF (403)")
            if response.status_code == 429:
                return Result.error("Rate limited by BuyMeaCoffee (429)")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to parse JSON response")

            message = data.get("message", "")

            # Success criteria (Status 200) -> Email exists
            if response.status_code == 200 and data.get("otp_login") is True:
                return Result.taken(url=show_url)

            # Failure criteria (Status 422) -> Email is free
            if response.status_code == 422 or "no account with the given" in message.lower():
                return Result.available(url=show_url)

            # Catching secondary validation array flags inside the errors object
            errors = data.get("errors", {})
            if "email" in errors and any("no account" in err.lower() for err in errors["email"]):
                return Result.available(url=show_url)

            return Result.error(f"Unexpected API State (HTTP {response.status_code})")

    except Exception as e:
        return Result.error(str(e))

async def validate_buymeacoffee(email: str) -> Result:
    return await _check(email)
