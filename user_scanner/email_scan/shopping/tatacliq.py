import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.tatadigital.com/api/v2/sso/check-email"
    show_url = "https://tatadigital.com"

    payload = {
        "email": email,
        "sendOtp": False,
    }

    headers = {
        "User-Agent": "okhttp/5.2.0",
        "Accept-Encoding": "gzip",
        "client_id": "TATACLIQ-ANDROID-APP",
        "appversion": "103.22.0",
        "appplatform": "android",
        "content-type": "application/json; charset=UTF-8",
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                user_type = data.get("userType")
                email_enrolled = data.get("emailEnrolled")

                if user_type in ["existing", "migrated"] or email_enrolled is True:
                    extra = {}
                    if user_type:
                        extra["user_type"] = user_type
                    if email_enrolled is not None:
                        extra["email_enrolled"] = email_enrolled
                    if data.get("emailVerified") is not None:
                        extra["email_verified"] = data["emailVerified"]
                    if data.get("phoneMasked"):
                        extra["phone_masked"] = data["phoneMasked"]
                    return Result.taken(extra=extra, url=show_url)

                if user_type == "new" or data.get("message") == "User is not found":
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_tatacliq(email: str) -> Result:
    """
    Tata CLiQ (Tata Neu / Tata Digital SSO) email validator.
    Checks check-email endpoint without sending OTP (sendOtp=False).
    """
    return await _check(email)
