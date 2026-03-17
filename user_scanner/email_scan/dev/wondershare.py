import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    csrf_url = "https://accounts.wondershare.com/api/v3/csrf-token"
    inspect_url = "https://accounts.wondershare.com/api/v3/account/inspect"
    show_url = "https://wondershare.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'x-lang': "en-us",
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': "?1",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://accounts.wondershare.com/m/login?source=&redirect_uri=https://www.wondershare.com/?source=&site=www.wondershare.com&verify=no",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:

            r_csrf = await client.get(csrf_url, headers=headers)
            if r_csrf.status_code != 200:
                return Result.error(f"Handshake failed: {r_csrf.status_code}")

            token = client.cookies.get("req_identity")

            if not token:
                return Result.error("req_identity cookie missing from handshake")

            inspect_headers = headers.copy()
            inspect_headers.update({
                'x-csrf-token': token,
                'Content-Type': "application/json",
                'origin': "https://accounts.wondershare.com",
                'referer': "https://accounts.wondershare.com/m/register"
            })

            payload = {"email": email}

            response = await client.put(
                inspect_url,
                content=json.dumps(payload),
                headers=inspect_headers
            )

            if response.status_code == 403:
                return Result.error("Caught by WAF (403)")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data_final = response.json()
            status_obj = data_final.get("data")

            if not isinstance(status_obj, dict):
                return Result.error("Invalid response data structure")

            status_code = status_obj.get("exist")

            # 1 = Registered, 2 = Not Registered
            if status_code == 1:
                return Result.taken(url=show_url)
            elif status_code == 2:
                return Result.available(url=show_url)

            return Result.error(f"Unexpected exist value: {status_code}")

    except Exception as e:
        return Result.error(e)


async def validate_wondershare(email: str) -> Result:
    return await _check(email)
