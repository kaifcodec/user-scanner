import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://thegay.com/api/signup.php"
    show_url = "https://thegay.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/x-www-form-urlencoded",
        'sec-ch-ua-platform': '"Android"',
        'Origin': "https://thegay.com",
        'Referer': "https://thegay.com/signup/",
        'Priority': "u=1, i"
    }

    payload = {
        'act': "signup",
        'usr': "th3_knight_l0st",
        'eml': email,
        'pwd': "youAr3Al0n3"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")

            if response.status_code == 429:
                return Result.error("Rate limited (429)")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()
            errors = data.get("errors", [])

            # We check if 'eml_occupied' is present in the list of error objects
            is_taken = any(err.get("code") == "eml_occupied" for err in errors)

            if is_taken:
                return Result.taken(url=show_url)

            # If we get tok_required but NOT eml_occupied, the email is available
            if any(err.get("code") == "tok_required" for err in errors):
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)

async def validate_thegay(email: str) -> Result:
    return await _check(email)
