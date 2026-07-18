import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword"
    show_url = "https://play.google.com/store/apps/details?id=com.whering.app"

    params = {
        'key': "AIzaSyBuo23oVhkHuZ_P7rKU1jUrMD8gJ95yVwk"
    }

    payload = {
        "email": email,
        "password": "igoh8h8g89y",
        "returnSecureToken": True,
        "clientType": "CLIENT_TYPE_ANDROID"
    }

    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TP1A.220624.021)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'X-Android-Package': "com.whering.app",
        'Accept-Language': "en-US",
        'X-Client-Version': "Android/Fallback/X24000000/FirebaseCore-Android",
        'X-Firebase-GMPID': "1:182334734580:android:b55d5ff0601be7971e5ea1"
    }

    async with httpx.AsyncClient(timeout=20.0, http2=True) as client:
        try:
            response = await client.post(url, params=params, json=payload, headers=headers, timeout=20.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 400:
                data = response.json()
                error_msg = data.get("error", {}).get("message", "")
                if error_msg == "EMAIL_NOT_FOUND":
                    return Result.available(url=show_url)
                elif error_msg == "INVALID_PASSWORD":
                    return Result.taken(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_whering(email: str) -> Result:
    """
    Whering email validator. Checks Firebase Auth verifyPassword endpoint.
    """
    return await _check(email)
