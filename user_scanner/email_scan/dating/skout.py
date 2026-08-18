import secrets
import uuid
import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.skout.com/validations/Users_NewUserCheck"
    show_url = "https://www.skout.com"

    android_id = secrets.token_hex(8)
    app_id = f"{uuid.uuid4()}?identifier=skout.prod"
    gpsa_id = f"{uuid.uuid4()}?identifier=skout.prod"
    appset_id = f"{uuid.uuid4()}?identifier=skout.prod"
    firebase_id = secrets.token_hex(16)

    params = {
        "email": email,
        "name": "notSet",
        "brand": "skout",
    }

    headers = {
        "User-Agent": "Skout/23201 Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TQ3A.230901.001) 4.12.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "kissapi-ad-id": "c66aefe62fa926b6e76dc1ebef756baf",
        "kissapi-ad-name": "Organic",
        "kissapi-ad-label": "",
        "kissapi-app-version": "23201",
        "kissapi-version": "1.36.0",
        "kissapi-device-os": "33",
        "kissapi-device-model": "Pixel 6",
        "tz": "UTC",
        "kissapi-device": "android",
        "kissapi-app-package-id": "com.skout.android",
        "kissapi-brand": "skout",
        "kissapi-apptype": "google",
        "kissapi-android-id": android_id,
        "kissapi-app-id": app_id,
        "kissapi-gpsa-id": gpsa_id,
        "kissapi-gpsa-on": "true",
        "kissapi-appset-id": appset_id,
        "firebase-analytics-app-instance-id": firebase_id,
        "accept-language": "en-US",
        "wifi": "0",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 409:
                data = response.json()
                msg = str(data.get("statusMessage", "")).lower()
                if "email already exists" in msg:
                    return Result.taken(url=show_url)

            if response.status_code == 200:
                data = response.json()
                if data.get("statusCode") == 200:
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_skout(email: str) -> Result:
    """
    Skout dating app email validator.
    Checks Users_NewUserCheck endpoint.
    """
    return await _check(email)
