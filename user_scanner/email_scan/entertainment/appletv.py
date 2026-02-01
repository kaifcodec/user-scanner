import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://idmsa.apple.com/appleauth/auth/federate"
    params = {'isRememberMeEnabled': "false"}
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Content-Type': "application/json",
        'X-Apple-Domain-Id': "2",
        'X-Apple-Locale': "en_us",
        'X-Apple-Auth-Context': "tv",
        'X-Requested-With': "XMLHttpRequest",
        'Origin': "https://idmsa.apple.com",
        'Referer': "https://idmsa.apple.com/",
    }
    payload = {
        "accountName": email,
        "rememberMe": False
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                params=params,
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if "primaryAuthOptions" in data:
                    return Result.taken()
                elif "primaryAuthOptions" not in data:
                    return Result.available()
                else:
                    return Result.error("Unexpected response body, report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Uexpected exception: {e}")


async def validate_appletv(email: str) -> Result:
    return await _check(email)
