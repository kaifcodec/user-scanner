import httpx
import json
import re
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    base_url = "https://www.fitnessblender.com"
    api_url = "https://www.fitnessblender.com/api/v1/validate/unique-email"
    show_url = "https://www.fitnessblender.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'Origin': "https://www.fitnessblender.com",
        'Referer': "https://www.fitnessblender.com/join",
        'X-Requested-With': "XMLHttpRequest",
        'Priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            # Step 1: Visit homepage to get cookies (XSRF-TOKEN and FB_SESSION)
            # Laravel sets these in the Set-Cookie header
            r_init = await client.get(base_url, headers=headers)
            
            if r_init.status_code != 200:
                return Result.error(f"Handshake failed: {r_init.status_code}")

            # Get the CSRF token from the cookies
            # Laravel allows using the XSRF-TOKEN cookie value as the x-csrf-token header
            csrf_token = client.cookies.get("XSRF-TOKEN")

            # If not in cookies, try to extract from the HTML script tag as a backup
            if not csrf_token:
                match = re.search(r'csrfToken:\s*"([^"]+)"', r_init.text)
                if match:
                    csrf_token = match.group(1)

            if not csrf_token:
                return Result.error("CSRF token not found")

            # Step 2: Post to the validation API
            headers['x-csrf-token'] = csrf_token
            headers['Content-Type'] = "application/json"

            payload = {
                "email": email,
                "force": 0
            }

            response = await client.post(
                api_url, 
                content=json.dumps(payload), 
                headers=headers
            )

            if response.status_code == 403:
                return Result.error("Caught by WAF (403)")

            if response.status_code == 419:
                return Result.error("CSRF Mismatch/Expired (419)")

            data = response.json()
            status = data.get("status")
            message = data.get("message", "").lower()

            # Logic: error + "already registered" = TAKEN
            if status == "error" and "already registered" in message:
                return Result.taken(url=show_url)

            # Logic: success + "ok" = AVAILABLE
            elif status == "success" and message == "ok":
                return Result.available(url=show_url)

            return Result.error(f"Unexpected response: {message}")

    except Exception as e:
        return Result.error(e)

async def validate_fitnessblender(email: str) -> Result:
    return await _check(email)
