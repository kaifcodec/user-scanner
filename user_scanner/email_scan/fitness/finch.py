import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getOobConfirmationCode"
    show_url = "https://www.finchcare.com/"  # Standard user dashboard reference

    params = {
        'key': "AIzaSyAtxGf97SHuNfYC0pjpTM4FSwPf08n9VF0"
    }

    payload = {
        "requestType": 1,
        "email": email,
        "androidInstallApp": False,
        "canHandleCodeInApp": False,
        "clientType": "CLIENT_TYPE_ANDROID"
    }

    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; RMX2193 Build/RP1A.200720.011)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'X-Android-Package': "com.finch.finch",
        'Accept-Language': "en-US",
        'X-Client-Version': "Android/Fallback/X23002001/FirebaseCore-Android"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, params=params, json=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by Google API Cloud WAF (403)")
            if response.status_code == 429:
                return Result.error("Rate limited by Google Identity Service (429)")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to parse JSON response payload")

            # Check for explicitly registered account (Status 200 and matches email key)
            if response.status_code == 200 and "email" in data:
                return Result.taken(url=show_url)

            # Check for available email (Status 400 with EMAIL_NOT_FOUND error array block)
            if response.status_code == 400:
                error_obj = data.get("error", {})
                msg = error_obj.get("message", "")

                if "email_not_found" in msg.lower():
                    return Result.available(url=show_url)

            return Result.error(f"Unexpected response footprint (HTTP {response.status_code})")

    except Exception as e:
        return Result.error(str(e))

async def validate_finch(email: str) -> Result:
    return await _check(email)
