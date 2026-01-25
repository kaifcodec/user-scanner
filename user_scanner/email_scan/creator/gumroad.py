import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    async with httpx.AsyncClient(http2=False, follow_redirects=True) as client:
        try:
            url1 = "https://gumroad.com/users/forgot_password/new"
            headers1 = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                'Accept-Encoding': "gzip, deflate, br, zstd",
                'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
                'sec-ch-ua-mobile': "?0",
                'sec-ch-ua-platform': '"Linux"',
                'upgrade-insecure-requests': "1",
                'referer': "https://www.google.com/",
                'accept-language': "en-US,en;q=0.9"
            }

            res1 = await client.get(url1, headers=headers1)
            html = res1.text

            csrf_match = re.search(
                r'authenticity_token&quot;:&quot;([^&]+)&quot;', html)
            if not csrf_match:
                csrf_match = re.search(
                    r'name="csrf-token" content="([^"]+)"', html)

            if not csrf_match:
                return Result.error("Failed to extract CSRF token")

            csrf_token = csrf_match.group(1)

            url2 = "https://gumroad.com/users/forgot_password"

            payload = {
                "user": {
                    "email": email
                }
            }

            headers2 = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                'Accept': "text/html, application/xhtml+xml",
                'Accept-Encoding': "gzip, deflate, br, zstd",
                'Content-Type': "application/json",
                'sec-ch-ua-platform': '"Linux"',
                'x-csrf-token': csrf_token,
                'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
                'x-inertia': "true",
                'sec-ch-ua-mobile': "?0",
                'x-requested-with': "XMLHttpRequest",
                'origin': "https://gumroad.com",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://gumroad.com/users/forgot_password/new",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=1, i"
            }

            response = await client.post(url2, json=payload, headers=headers2)

            data = response.json()
            flash_msg = data.get("props", {}).get(
                "flash", {}).get("message", "")

            if "An account does not exist" in flash_msg:
                return Result.available()
            elif "An account does not exist" not in flash_msg:
                return Result.taken()
            else:
                return Result.error(f"Unexpected status: {response.status_code}")

        except Exception as e:
            return Result.error(f"unexpected exception: {e}")


async def validate_gumroad(email: str) -> Result:
    return await _check(email)
