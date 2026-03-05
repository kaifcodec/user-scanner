import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://jsso.indiatimes.com/sso/crossapp/identity/web/checkUserExists"
    show_url = "https://gaana.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'channel': "gaana.com",
        'platform': "WAP",
        'sdkversion': "0.7.3",
        'isjssocrosswalk': "true",
        'origin': "https://gaana.com",
        'referer': "https://gaana.com/",
        'priority': "u=1, i"
    }

    payload = {
        "identifier": email
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            
            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")
            
            if response.status_code == 429:
                return Result.error("Rate limited by JSSO (429)")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()
            user_status = data.get("data", {}).get("status", "")

            if user_status == "VERIFIED_EMAIL" or user_status == "UNVERIFIED_EMAIL":
                return Result.taken(url=show_url)
            
            elif data.get("status") == "SUCCESS":
                return Result.available(url=show_url)

            else:
                return Result.error("Unexpected response body structure, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)

async def validate_gaana(email: str) -> Result:
    return await _check(email)
