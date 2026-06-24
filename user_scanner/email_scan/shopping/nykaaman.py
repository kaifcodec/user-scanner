import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://www.nykaaman.com/app-api/index.php/customer/check_existence"
    show_url = "https://www.nykaaman.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Brave";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        'sec-ch-ua-mobile': "?1",
        'sec-gpc': "1",
        'accept-language': "en-US,en;q=0.9",
        'origin': "https://www.nykaaman.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': f"{show_url}?ptype=auth&root=myAccount_topBar",
        'Cookie': "storeId=men"
    }

    params = {
        'catalog_tag_filter': "men"
    }

    payload = {
        'email': email,
        'platform': "web",
        'captcha_type': "v3"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Send payload using standard form encoding data format
            response = await client.post(url, params=params, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF (403)")
            if response.status_code == 429:
                return Result.error("Rate limited (429)")
            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to parse JSON response")

            inner_response = data.get("response", {})
            is_exists = inner_response.get("is_exists")

            # Evaluate direct boolean flag or match validation strings
            if is_exists is True or "already registered" in inner_response.get("message", "").lower():
                return Result.taken(url=show_url)

            if is_exists is False or "welcome to nykaa" in inner_response.get("message", "").lower():
                return Result.available(url=show_url)

            return Result.error("Unexpected JSON response structure")

    except Exception as e:
        return Result.error(str(e))

async def validate_nykaaman(email: str) -> Result:
    return await _check(email)
