import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://wix.com"
    url = "https://users.wix.com/wix-users/v1/userAccountsByEmail"

    payload = {
        "email": email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'x-wix-client-artifact-id': "login-react-app",
        'origin': "https://users.wix.com",
        'referer': "https://users.wix.com/signin/signup",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 200:
                data = response.json()
                if "accountsData" in data and len(data.get("accountsData", [])) > 0:
                    return Result.taken(url=show_url)
                return Result.error("Unexpected response body structure, report it via GitHub issues")

            elif response.status_code == 404:
                return Result.available(url=show_url)

            elif response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")

            else:
                return Result.error(f"Unexpected status code: {response.status_code}, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_wix(email: str) -> Result:
    return await _check(email)
