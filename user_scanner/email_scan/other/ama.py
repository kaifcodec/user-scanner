import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://fsso.ama-assn.org/api/resetPassword"
    show_url = "https://www.ama-assn.org"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Brave";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': "?1",
        'Sec-GPC': "1",
        'Accept-Language': "en-US,en;q=0.8",
        'Origin': "https://fsso.ama-assn.org",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': show_url,
        'Cookie': "IV_JCT=%2Flogin;"
    }

    payload = {
        "emailAddressOrPhone": email,
        "fedType": "oAuth",
        "returnUrl": "/AMAresources",
        "refererUrl": "/AMAresources",
        "successUrl": "https://www.ama-assn.org/",
        "appCxUrl": "https://www.ama-assn.org/"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF (403)")
            if response.status_code == 429:
                return Result.error("Rate limited (429)")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to parse JSON response")

            msg = data.get("message", "")
            inner_code = str(data.get("httpCode", ""))

            if inner_code == "200" and "sent successfully" in msg.lower():
                return Result.taken(url=show_url)

            if inner_code == "202" or "not found" in msg.lower() or "please use an existing account" in msg.lower():
                return Result.available(url=show_url)

            return Result.error(f"Logic Mismatch - Code: {inner_code} | Msg: {msg[:50]}")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))

async def validate_ama(email: str) -> Result:
    return await _check(email)
