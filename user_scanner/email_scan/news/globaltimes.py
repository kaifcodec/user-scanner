import httpx
import json
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    url = "https://enapp.globaltimes.cn/api/user/login"

    payload = {
        "mail": email,
        "password": "21A5F558F45BE7FEA45A47EF4CAEC71B",
        "sensorsDistinctId": "",
        "sensorsAnonymousId": ""
    }

    headers = {
        'User-Agent': get_random_user_agent(),
        'Content-Type': "application/json;charset=UTF-8",
        'Token': "null",
        'Vcode': "232",
        'Origin': "https://enapp.globaltimes.cn",
        'Referer': "https://enapp.globaltimes.cn/web/login",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            data = response.json()
            message = data.get("msg", "")

            taken_indicators = [
                "password is incorrect",
                "account will be locked",
                "number of retries has reached the maximum"
            ]

            if any(indicator in message for indicator in taken_indicators):
                return Result.taken()

            if "don't recognize this account" in message:
                return Result.available()

            return Result.error("Unexpected response body, report it on github")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out!")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_globaltimes(email: str) -> Result:
    return await _check(email)
