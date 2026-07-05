import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://api.interntp.com/v1/app/user/register"
    show_url = "https://www.aiscore.com/"

    headers = {
        'User-Agent': "AiScore/4.2.4 (realme;RMX2193;Android11)",
        'Accept-Encoding': "gzip",
        'platform': "1",
        'channel': "play Google play",
        'ver': "4.2.4",
        'timezone': "05:30",
        'time': "1783232760"
    }

    # Note: The original request used form data payload, not JSON
    payload = {
        'email': email,
        'password': "Nopi0fish",
        'lang': "2"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Blocked by AiScore perimeter security (403)")
            if response.status_code != 200:
                return Result.error(f"Target API responded with status code {response.status_code}")

            # Checking the raw content text for the explicit binary-embedded error string
            # We use 'errors-tolerant' decoding just in case the surrounding binary bytes choke standard UTF-8
            response_text = response.content.decode('utf-8', errors='ignore')

            # Explicit Validation Mapping:
            if "The email is existed" in response_text:
                return Result.taken(url=show_url)
            
            # If it's a 200 OK but doesn't contain the 'existed' error, it's returning the registration token sequence
            if response_text:
                return Result.available(url=show_url)

            return Result.error("Empty or unparsable binary envelope received")

    except Exception as e:
        return Result.error(str(e))

async def validate_aiscore(email: str) -> Result:
    return await _check(email)
