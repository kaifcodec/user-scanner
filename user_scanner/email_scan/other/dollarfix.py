import base64
import secrets
import httpx
from user_scanner.core.result import Result


def _generate_firebase_uuid() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(16)).decode("utf-8").rstrip("=").replace("-", "_")


async def _check(email: str) -> Result:
    url = "https://api.dollarfix.com/core-userinfo/user_center/apkLogin"
    show_url = "https://dollarfix.com"

    payload = {
        "password": "generic_password_123",
        "verifiable_type": 1,
        "user_name": email
    }

    uuid_val = _generate_firebase_uuid()
    firebase_token = f"{uuid_val}:APA91bFmZorXu14j6IauzmcISJNDuPds2wd5VAO35UFBLNAnzE7NA242XqLF46kZqZ-k9Q5Io7COOA5WbWScOwOFYqCc_UxqIqfxH486OYDwh3iQslz6Xuk"

    headers = {
        'User-Agent': "okhttp/4.10.0",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'client': "1",
        'appversion': "1.8.9.1",
        'phonemodel': "Pixel 6",
        'phonesystem': "13",
        'appid': "9205",
        'appname': "DollarFix",
        'headsn': "",
        'token': "",
        'uuid': uuid_val,
        'firebasetoken': firebase_token,
        'zone': "GMT+0:00",
        'lang': "en",
        'content-type': "application/json; charset=utf-8"
    }

    async with httpx.AsyncClient(timeout=15.0, http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                msg = data.get("msg", "")

                if msg in ["Incorrect password", "not set password"]:
                    return Result.taken(url=show_url)
                elif msg == "The user does not exist.":
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_dollarfix(email: str) -> Result:
    """
    DollarFix email validator.
    """
    return await _check(email)
