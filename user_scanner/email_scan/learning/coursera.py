import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://coursera.org"
    url = "https://www.coursera.org/api/userAccounts.v1"

    params = {
        'action': "getLoginMethods",
        'email': email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'X-Requested-With': "XMLHttpRequest",
        'X-Coursera-Application': "front-page",
        'Origin': "https://www.coursera.org",
        'Referer': "https://www.coursera.org/?authMode=signup"
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(url, params=params, json={}, headers=headers)
            data = response.json()

            if "loginMethods" not in data:
                return Result.error("Missing 'loginMethods' in response, report it on github")

            methods = data["loginMethods"]

            if not isinstance(methods, list):
                return Result.error(f"Unexpected data type for loginMethods: {type(methods)}, report it on github")
            if len(methods) > 0:
                return Result.taken(url=show_url)
            else:
                return Result.available(url=show_url)

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out (Coursera)")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Coursera)")
    except Exception as e:
        return Result.error(e)


async def validate_coursera(email: str) -> Result:
    return await _check(email)
