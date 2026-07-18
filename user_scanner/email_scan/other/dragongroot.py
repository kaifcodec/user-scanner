import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://hayat.dragongroot.com/api/auth/signup/send-otp"
    show_url = "https://dragongroot.com"

    payload = {
        "email": email
    }

    headers = {
        'User-Agent': "okhttp/4.12.0",
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
                if data.get("success") is False and data.get("message") == "An account with this email already exists":
                    return Result.taken(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            if response.status_code == 200:
                data = response.json()
                if data.get("success") is True and data.get("message") == "OTP sent to your email":
                    return Result.available(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_dragongroot(email: str) -> Result:
    """
    Dragongroot email validator. Note: This will send a signup OTP email if it is available.
    """
    return await _check(email)
