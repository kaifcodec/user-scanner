import httpx
import re
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url_login = "https://luarocks.org/login"
    url_forgot = "https://luarocks.org/user/forgot_password"
    show_url = "https://luarocks.org"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'sec-ch-ua': '"Brave";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        'sec-ch-ua-mobile': "?1",
        'sec-ch-ua-platform': '"Android"',
        'Upgrade-Insecure-Requests': "1",
        'Sec-GPC': "1",
        'Accept-Language': "en-US,en;q=0.9",
        'Origin': "https://luarocks.org",
        'Referer': url_forgot
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:

            # Hit login endpoint directly to grab token cookie and search form csrf
            init_res = await client.get(url_login, headers=headers)
            if init_res.status_code != 200:
                return Result.error(f"Failed to load validation frame: {init_res.status_code}")

            csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', init_res.text)
            if not csrf_match:
                return Result.error("Could not parse LuaRocks state CSRF token")

            csrf_token = csrf_match.group(1)

            # Push password reset form validation check
            payload = {
                'csrf_token': csrf_token,
                'email': email
            }

            response = await client.post(url_forgot, data=payload, headers=headers)
            response_text = response.text.lower()

            # Parse structural text outputs using broad substrings to prevent template entity escaping bugs
            if "password reset link has been sent" in response_text:
                return Result.taken(url=show_url)

            # Checking for standard, stripped, and HTML-escaped string formats simultaneously
            if "don't know anyone" in response_text or "don&#39;t know anyone" in response_text or "know anyone with that email" in response_text:
                return Result.available(url=show_url)

            return Result.error("Unexpected target response markup signature")

    except Exception as e:
        return Result.error(str(e))

async def validate_luarocks(email: str) -> Result:
    return await _check(email)
