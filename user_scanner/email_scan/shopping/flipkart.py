import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://1.rome.api.flipkart.com/1/action/view"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'X-User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36 FKUA/msite/0.0.3/msite/Mobile channelType/undefined",
        'Origin': "https://www.flipkart.com",
        'Referer': "https://www.flipkart.com/"
    }

    payload = {
        "actionRequestContext": {
            "type": "LOGIN_IDENTITY_VERIFY",
            "loginIdPrefix": "",
            "loginId": email,
            "clientQueryParamMap": {"ret": "/"},
            "loginType": "EMAIL",
            "verificationType": "PASSWORD",
            "screenName": "LOGIN_V4_EMAIL",
            "sourceContext": "DEFAULT"
        }
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            response_text = response.text

            if "Looks like you're new here!" in response_text:
                return Result.available()

            if "LOGIN_P_CHECK" in response_text or '"statusSuccess":true' in response_text:
                return Result.taken()

            return Result.taken()

        except Exception as e:
            return Result.error(e)

async def validate_flipkart(email: str) -> Result:
    return await _check(email)
