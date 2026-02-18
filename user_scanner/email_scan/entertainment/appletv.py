import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    show_url = "https://tv.apple.com"
    url = "https://idmsa.apple.com/appleauth/auth/federate"
    params = {'isRememberMeEnabled': "false"}
    headers = {
        'User-Agent': get_random_user_agent(),
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
                    return Result.taken(url=show_url)
                elif "primaryAuthOptions" not in data:
                    return Result.available(url=show_url)
                else:
                    return Result.error("Unexpected response body, report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected exception: {e}")


async def validate_appletv(email: str) -> Result:
    return await _check(email)
