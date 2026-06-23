import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://www.hackerrank.com/auth/valid_email"
    show_url = "https://www.hackerrank.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        'sec-ch-ua-mobile': "?1",
        'sec-gpc': "1",
        'accept-language': "en-US,en;q=0.9",
        'origin': "https://www.hackerrank.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': show_url,
        'priority': "u=1, i"
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by Cloudflare/WAF (403)")
            if response.status_code == 429:
                return Result.error("Rate limited (429)")
            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to parse JSON response")

            status = data.get("status")
            internal_code = data.get("internal_status_code")
            errors_msg = data.get("errors", "")

            # If status is False or explicit strings match -> Taken
            if status is False or internal_code == "already_registered" or "already registered" in str(errors_msg).lower():
                return Result.taken(url=show_url)

            # If status is True -> Free to register
            if status is True:
                return Result.available(url=show_url)

            return Result.error("Unexpected response payload schema")

    except Exception as e:
        return Result.error(str(e))

async def validate_hackerrank(email: str) -> Result:
    return await _check(email)
