import httpx
import uuid
import secrets
from user_scanner.core.result import Result


def _generate_uuid() -> str:
    """Generate standard UUID v4 string."""
    return str(uuid.uuid4())


def _generate_install_id() -> str:
    """Generate random 23-character string for InstallId."""
    return secrets.token_hex(11) + "a"


def _generate_anonymous_id() -> str:
    """Generate random anonymousId string."""
    return secrets.token_hex(6) + ".0136"


async def _check(email: str) -> Result:
    url = "https://api.premom.com/user/user/sign/up"
    show_url = "https://premom.com"

    phone_id = _generate_uuid()
    install_id = _generate_install_id()
    anonymous_id = _generate_anonymous_id()

    payload = {
        "bindAnonymous": False,
        "anonymousId": anonymous_id,
        "password": "generic_password_123",
        "protocolInfo": [
            {
                "protocolType": "TERMS_OF_SERVICE",
                "protocolUrl": "https://api.premom.com/app/webview/protocol?version=38&protocolType=TERMS_OF_SERVICE",
                "publishDate": "2025-12-25 15:47:01",
                "version": 38
            },
            {
                "protocolType": "PRIVACY_POLICY",
                "protocolUrl": "https://api.premom.com/app/webview/protocol?version=76&protocolType=PRIVACY_POLICY",
                "publishDate": "2026-02-16 14:27:45",
                "version": 76
            }
        ],
        "OSType": "Pixel6_33",
        "phoneID": phone_id,
        "processType": "",
        "email": email
    }

    headers = {
        'User-Agent': "Premom/1.104.0 (Google Pixel 6; Android 13; GMT+00:00)",
        'Connection': "Keep-Alive",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'country': "US",
        'appVersion': "1.104.0",
        'os': "Android 13",
        'city': "New York",
        'timezone': "America/New_York",
        'Charset': "UTF-8",
        'language': "0",
        'appVersionCode': "388",
        'System-Language': "en",
        'system-language-code': "en_US",
        'apiVersion': "99",
        'InstallId': install_id,
        'device': "Pixel 6",
        'System-Country': "US"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 510:
                data = response.json()
                code = data.get("code")
                msg = data.get("message", "")

                if code == "SIGN_DUPLICATED_EMAIL" or "already been registered" in msg:
                    return Result.taken(url=show_url)
                elif code == "ERR_VALIDATE_ERROR" or "Empty first name" in msg:
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_premom(email: str) -> Result:
    """
    Premom email validator. Checks sign up endpoint.
    """
    return await _check(email)
