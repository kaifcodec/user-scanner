import httpx
import time
from user_scanner.core.result import Result

def _generate_timestamp() -> str:
    """Generates a current Unix timestamp in milliseconds as a string."""
    return str(int(time.time() * 1000))

async def _check(email: str) -> Result:
    url = "https://global.apis.naver.com/lineWebtoon/webtoon/emailValidationV1"
    show_url = "https://www.webtoons.com/"

    headers = {
        'User-Agent': "nApps (Android 11; RMX2193; linewebtoon; 3.9.6)",
        'Accept-Encoding': "gzip",
        'content-type': "application/json; charset=UTF-8"
    }

    params = {
        'serviceZone': "GLOBAL",
        'v': "1",
        'language': "en",
        'locale': "en",
        'platform': "APP_ANDROID",
        'msgpad': "1783181747712",  # need to be static or md fails
        'md': "xNlchGIXRvNEtp7TF1LkR5X3a6A="  # Preserved static hash per requirement
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, params=params, json=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by Naver WAF / Cloudflare Mitigation (403)")
            if response.status_code == 429:
                return Result.error("Rate limited by Webtoon API (429)")
            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to parse JSON response footprint")

            # Drilling down the nested Naver API JSON response layer
            message_obj = data.get("message", {})
            result_obj = message_obj.get("result", {})

            valid = result_obj.get("valid")

            # Target validation logic: valid is False or code states DUPLICATED -> Taken
            if valid is False:
                return Result.taken(url=show_url)

            # Target validation logic: valid is True -> Available
            if valid is True:
                return Result.available(url=show_url)

            return Result.error("Unexpected validation fields inside inner payload")

    except Exception as e:
        return Result.error(str(e))

async def validate_linewebtoon(email: str) -> Result:
    return await _check(email)
