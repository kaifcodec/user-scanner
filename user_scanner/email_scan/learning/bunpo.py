import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getOobConfirmationCode"
    show_url = "https://play.google.com/store/apps/details?id=com.bunpoapp"

    params = {
        'key': "AIzaSyAxg8aXqILmTAN_OOAGIRt0IL6nkQyj3p8"
    }

    payload = {
        "requestType": 1,
        "email": email,
        "androidInstallApp": False,
        "canHandleCodeInApp": False,
        "clientType": "CLIENT_TYPE_ANDROID"
    }

    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TP1A.220624.021)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'X-Android-Package': "com.bunpoapp",
        'Accept-Language': "en-, en-US",
        'X-Client-Version': "Android/Fallback/X23000000/FirebaseCore-Android"
    }

    async with httpx.AsyncClient(timeout=15.0, http2=True) as client:
        try:
            response = await client.post(url, params=params, json=payload, headers=headers, timeout=15.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 400:
                data = response.json()
                error_msg = data.get("error", {}).get("message", "")
                if error_msg == "EMAIL_NOT_FOUND":
                    return Result.available(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            if response.status_code == 200:
                data = response.json()
                if data.get("kind") == "identitytoolkit#GetOobConfirmationCodeResponse":
                    return Result.taken(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_bunpo(email: str) -> Result:
    """
    Bunpo email validator. Note: This will send a password reset email if it exists.
    """
    return await _check(email)
