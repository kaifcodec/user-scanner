import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.sskkjp1l6cx7.link/api/v1/user/signup/send_password_renewal_code"
    show_url = "https://superlive.io"

    headers = {
        "User-Agent": "SuperLive/2.38.1 (Pixel 6; Android 13; Scale/mdpi)",
        "Accept-Encoding": "gzip",
        "device-id": "08f890cd6e0b9235cde1d50522f5f4ed",
        "Content-Type": "application/json; charset=UTF-8",
    }

    payload = {
        "email": email,
        "force_new": True,
        "client_params": {
            "adid": "c66aefe62fa926b6e76dc1ebef756baf",
            "adjust_attribution_data": {
                "adgroup": "",
                "adid": "c66aefe62fa926b6e76dc1ebef756baf",
                "campaign": "",
                "click_label": "",
                "creative": "",
                "network": "Organic",
                "tracker_name": "Organic",
                "tracker_token": "mii5ej6",
            },
            "android_id": "1db33b89299a9d90",
            "app_language": "en",
            "brand_name": "google",
            "carrier": "",
            "currency_code": "_",
            "device_language": "en",
            "device_preferred_languages": ["en"],
            "initial_country": "US",
            "display_density": "420 dpi",
            "display_ratio": "16:9",
            "display_resolution_height": 1920,
            "display_resolution_width": 1080,
            "display_size": "6.0 inch",
            "firebase_analytics_id": "ec9377988825dec03f2335b01dc32179",
            "ga_session_id": "1786979772",
            "gps_adid": "0e1aa4df-0e53-4cb6-8a37-b73fff9a27de",
            "installation_id": "5d27f697-91ec-407e-a5e3-cbf2e0e1e66b",
            "mac": "None",
            "marketing_name": "Pixel 6",
            "model_name": "Pixel 6",
            "network_type": "WIFI",
            "os_hardware_model": "unknown",
            "os_type": "android",
        },
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 400:
                data = response.json()
                err = data.get("error", {})
                msg = str(err.get("message", "")).lower()

                if "no registered users with this email" in msg:
                    return Result.available(url=show_url)

                if "attempt limit reached" in msg or err.get("code") == 12:
                    return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                if "password_renewal_id" in data:
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_superlive(email: str) -> Result:
    """
    SuperLive email validator.
    Checks send_password_renewal_code endpoint.
    Loud module because password renewal codes are sent to registered accounts.
    """
    return await _check(email)
