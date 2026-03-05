import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://emirates.com"
    url = "https://www.emirates.com/service/ekl/validate-email"

    params = {
        'data': "null"
    }

    payload = {
        "emailAddress": email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145\", \"Chromium\";v=\"145"',
        'sec-ch-ua-mobile': "?1",
        'origin': "https://www.emirates.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, params=params, content=json.dumps(payload), headers=headers)
            status = response.status_code

            if status == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if status == 200:
                data = response.json()
                body = data.get("body", {})
                errors = body.get("errors", [])

                if any(err.get("code") == "program.member.EmailExistsForAnotherMember" for err in errors):
                    return Result.taken(url=show_url)

                if data.get("status") is True:
                    return Result.available(url=show_url)

                return Result.available(url=show_url)

            if status == 429:
                return Result.error("Rate limited by Emirates")

            return Result.error(f"Unexpected status code: {status}")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except Exception as e:
        return Result.error(e)


async def validate_emirates(email: str) -> Result:
    return await _check(email)
