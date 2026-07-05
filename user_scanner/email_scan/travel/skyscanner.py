import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://mobile.ds.skyscanner.net/g/traveller-auth-service/accounts/v2/search"
    show_url = "https://www.skyscanner.net/"

    headers = {
        'User-Agent': "Skyscanner/7.198 (Android 11; Mobile)",
        'Accept-Encoding': "gzip",
        'origin': "https://www.skyscanner.net",
        'x-skyscanner-client': "skyscanner_android_app",
        'x-skyscanner-client-version': "7.198",
        'x-skyscanner-client-type': "net.skyscanner.android.main",
        'x-skyscanner-authenticated': "false",
        'x-skyscanner-device-os-type': "Android",
        'x-skyscanner-device-os-version': "11",
        'x-skyscanner-device': "Android-phone",
        'x-skyscanner-device-class': "phone",
        'x-skyscanner-client-network-type': "WIFI",
        'x-skyscanner-currency': "USD",
        'x-skyscanner-locale': "en-US",
        'x-skyscanner-market': "US",
        'content-type': "application/json; charset=UTF-8"
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            # Edge Mitigation for WAF / Rate limits
            if response.status_code == 403:
                return Result.error("Caught by Skyscanner anti-bot/WAF edge (403)")
            if response.status_code == 429:
                return Result.error("Rate limit tripped on gateway (429)")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to decode response body as JSON")


            # HTTP 200 - Registered Account
            if response.status_code == 200:
                # Confirming it actually has authentication providers assigned
                if "providers" in data and isinstance(data["providers"], list) and len(data["providers"]) > 0:
                    return Result.taken(url=show_url)
                return Result.error("200 OK returned but 'providers' array missing or empty")

            # HTTP 404 - Available Account
            if response.status_code == 404:
                # Verifying it matches the explicit 404 error structural footprint
                if data.get("code") == 404 or "Not Found" in data.get("message", ""):
                    return Result.available(url=show_url)
                return Result.error("404 status received but body content doesn't match expected error schema")

            return Result.error(f"Unexpected response condition (HTTP {response.status_code})")

    except Exception as e:
        return Result.error(str(e))

async def validate_skyscanner(email: str) -> Result:
    return await _check(email)
