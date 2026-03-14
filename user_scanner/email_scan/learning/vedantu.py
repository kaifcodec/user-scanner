import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://user.vedantu.com/user/preLoginVerification"
    show_url = "https://www.vedantu.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json;charset=UTF-8",
        'sec-ch-ua-platform': '"Linux"',
        'Origin': "https://www.vedantu.com",
        'Referer': "https://www.vedantu.com/",
        'Priority': "u=1, i"
    }

    payload = {
        "email": email,
        "phoneCode": None,
        "phoneNumber": None,
        "version": 2,
        "ver": 1.033,
        "token": "",
        "sType": "",
        "sValue": "",
        "event": "NEW_FLOW"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url, 
                content=json.dumps(payload), 
                headers=headers
            )

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if response.status_code == 429:
                return Result.error("Rate limited by Vedantu (429)")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()

            # Primary check using the emailExists key
            if data.get("emailExists") is True:
                masked_phone = data.get("phone")
                if masked_phone:
                    # Passing the masked phone number to the result
                    return Result.taken(url=show_url, extra=f"Phone: {masked_phone}")
                return Result.taken(url=show_url)

            elif data.get("emailExists") is False:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)

async def validate_vedantu(email: str) -> Result:
    return await _check(email)
