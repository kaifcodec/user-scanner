import httpx
from user_scanner.core.result import Result
async def _check(email: str) -> Result:
    url = "https://api.numiva.me/api/auth/register"
    show_url = "https://numsify.com"
    payload = {
        "email": email,
        "password": "everyone_thought_i_am_heartless",  # Intentionally fails strength check (no number)
        "first_name": "theknight",
        "last_name": "nevergivesup"
    }
    headers = {
        'User-Agent': "Dart/3.11 (dart:io)",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'x-device-name': "Android:google-Pixel 6-13",
        'lang': "en",
        'authorization': "Bearer null",
        'x-app-version': "1.4.53+73"
    }
    async with httpx.AsyncClient(timeout=15.0, http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)
            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)
            data = response.json()
            error_data = data.get("error", {})
            error_msg = error_data.get("message", "")
            if "password must contain at least one number" in error_msg:
                return Result.available(url=show_url)
            elif "email already registered" in error_msg:
                return Result.taken(url=show_url)
            return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)
        except Exception as e:
            return Result.error(e, url=show_url)
async def validate_numsify(email: str) -> Result:
    """
    Numsify email validator. Checks registration endpoint without sending an email.
    """
    return await _check(email)
