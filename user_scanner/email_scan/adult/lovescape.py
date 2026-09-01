import httpx
import re
from user_scanner.core.result import Result


async def _get_guest_uuid(client: httpx.AsyncClient) -> str:
    """Get a guest UUID from the config endpoint."""
    try:
        config_url = "https://lovescape.com/api/front/config"
        config_response = await client.get(config_url)
        if config_response.status_code == 200:
            config_data = config_response.json()
            return config_data.get("guestUuid", "")
    except (httpx.HTTPError, httpx.TimeoutException):
        # Config endpoint may be unavailable; fallback to empty string
        pass
    return ""


async def _check(email: str) -> Result:
    url = "https://lovescape.com/api/front/auth/signup"
    show_url = "https://lovescape.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json;charset=UTF-8",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': "?1",
        'Origin': "https://lovescape.com",
        'Referer': "https://lovescape.com/signup",
        'Priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step 1: Get guest UUID from config endpoint
            guest_uuid = await _get_guest_uuid(client)

            # If no guest UUID, try to get it from the signup page
            if not guest_uuid:
                try:
                    page_response = await client.get("https://lovescape.com/signup")
                    if 'set-cookie' in page_response.headers:
                        cookies = page_response.headers.get('set-cookie', '')
                        uuid_match = re.search(r'guestUuid=([^;]+)', cookies)
                        if uuid_match:
                            guest_uuid = uuid_match.group(1)
                except (httpx.HTTPError, httpx.TimeoutException):
                    # Signup page may be unavailable; continue with empty UUID
                    pass

            # Step 2: Build payload with guest UUID
            payload = {
                "username": "_W3ak3n3d_Cut3n3ss86541",
                "email": email,
                "password": "igy8868yiyy",
                "recaptcha": "",
                "fingerprint": "",
                "modelName": "",
                "isPwa": False,
                "affiliateId": "",
                "trafficSource": "",
                "isUnThrottled": False,
                "hasActionParam": False,
                "source": "page_signup",
                "device": "mobile",
                "deviceName": "Android Mobile",
                "browser": "Chrome",
                "os": "Android",
                "locale": "en",
                "authType": "native",
                "guestUuid": guest_uuid,
                "ampl": {
                    "ep": {
                        "source": "page_signup",
                        "startSessionUrl": "/create-ai-sex-girlfriend/style",
                        "firstVisitedUrl": "/create-ai-sex-girlfriend/style",
                        "referrerHost": "hakurei.us-cdnbo.org",
                        "referrerId": "us-cdnbo",
                        "signupUrl": "/signup",
                        "page": "signup",
                        "project": "Lovescape",
                        "isCookieAccepted": True,
                        "displayMode": "browser"
                    },
                    "up": {
                        "source": "page_signup",
                        "startSessionUrl": "/create-ai-sex-girlfriend/style",
                        "firstVisitedUrl": "/create-ai-sex-girlfriend/style",
                        "referrerHost": "hakurei.us-cdnbo.org",
                        "referrerId": "us-cdnbo",
                        "signupUrl": "/signup"
                    },
                    "device_id": "",
                    "session_id": 1774884558258
                }
            }

            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("403 Forbidden")

            data = response.json()
            error_msg = data.get("error", "")

            # Check for guest UUID error
            if "Guest uuid is required" in error_msg:
                return Result.error("Guest UUID required - try again (session issue)")

            if "Email is already used" in error_msg:
                return Result.taken(url=show_url)

            if "Username is already used" in error_msg:
                return Result.available(url=show_url)

            return Result.error(f"Unexpected: {error_msg}")

    except (httpx.HTTPError, httpx.TimeoutException) as e:
        return Result.error(f"Network error: {str(e)}")
    except Exception as e:
        return Result.error(str(e))


async def validate_lovescape(email: str) -> Result:
    return await _check(email)