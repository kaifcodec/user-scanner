import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://lovescape.com/api/front/auth/signup"
    show_url = "https://lovescape.com"

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

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "text/plain;charset=UTF-8",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': "?1",
        'Origin': "https://lovescape.com",
        'Referer': "https://lovescape.com/signup",
        'Priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 403:
                return Result.error("403")

            data = response.json()
            error_msg = data.get("error", "")

            if "Email is already used" in error_msg:
                return Result.taken(url=show_url)

            if "recaptcha is required" in error_msg:
                return Result.available(url=show_url)

            return Result.error(f"Unexpected: {error_msg}")

    except Exception as e:
        return Result.error(e)

async def validate_lovescape(email: str) -> Result:
    return await _check(email)
