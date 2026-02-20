import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://www.deezer.com"
    gw_url = "https://www.deezer.com/ajax/gw-light.php"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept-Encoding': "identity",
        'Content-Type': "text/plain;charset=UTF-8",
        'Origin': "https://account.deezer.com",
        'Referer': "https://account.deezer.com/"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            handshake_params = {
                'method': "deezer.getUserData",
                'input': "3",
                'api_version': "1.0",
                'api_token': ""
            }
            handshake_payload = {"APP_NAME": "Deezer"}

            r_handshake = await client.post(
                gw_url,
                params=handshake_params,
                content=json.dumps(handshake_payload),
                headers=headers
            )

            if r_handshake.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403) during Handshake")

            handshake_data = r_handshake.json()
            api_token = handshake_data.get("results", {}).get("checkForm")

            if not api_token:
                return Result.error("Failed to retrieve api_token (checkForm) from Deezer")

            validate_params = {
                'method': "user_checkRegisterConstraints",
                'input': "3",
                'api_version': "1.0",
                'api_token': api_token
            }

            validate_payload = {
                "APP_NAME": "Deezer",
                "EMAIL": email
            }

            response = await client.post(
                gw_url,
                params=validate_params,
                content=json.dumps(validate_payload),
                headers=headers
            )

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403) during Validation")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()
            errors = data.get("results", {}).get("errors", {})

            if errors.get("email", {}).get("error") == "email_already_used":
                return Result.taken(url=show_url)

            elif "country" in errors and "email" not in errors:
                return Result.available(url=show_url)

            else:
                return Result.error("Unexpected response body structure, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except Exception as e:
        return Result.error(e)


async def validate_deezer(email: str) -> Result:
    return await _check(email)
