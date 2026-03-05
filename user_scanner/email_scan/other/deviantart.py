import httpx
import re
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    show_url = "https://www.deviantart.com"
    join_page = "https://www.deviantart.com/join/"
    verify_url = "https://www.deviantart.com/_sisu/do/signup2"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'upgrade-insecure-requests': "1"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            r_home = await client.get(show_url, headers=headers)
            if r_home.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403) during Handshake 1")

            r_join = await client.get(join_page, headers=headers)
            if r_join.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403) during Handshake 2")

            csrf_match = re.search(r"window\.__CSRF_TOKEN__\s*=\s*'([^']+)'", r_join.text)
            if not csrf_match:
                return Result.error("Failed to extract CSRF token from window variable")
            
            csrf_token = csrf_match.group(1)

            payload = {
                'referer': "https://www.deviantart.com/",
                'referer_type': "",
                'csrf_token': csrf_token,
                'join_mode': "email",
                'oauth': "0",
                'email': email,
                'password': "",
                'username': "scanner_test_99",
                'dobMonth': "6",
                'dobDay': "6",
                'dobYear': "1998"
            }

            headers.update({
                'origin': "https://www.deviantart.com",
                'referer': "https://www.deviantart.com/join/"
            })

            response = await client.post(verify_url, data=payload, headers=headers)
            status = response.status_code

            if status == 403:
                return Result.error("Caught by WAF or IP Block (403) during Validation")

            resp_text = response.text

            if 'id="email-error">That email address is already in use.' in resp_text:
                return Result.taken(url=show_url)
            
            if 'id="email-error"' not in resp_text:
                return Result.available(url=show_url)

            if status == 429:
                return Result.error("Rate limited by DeviantArt")

            return Result.error(f"Unexpected response content or status: {status}")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except Exception as e:
        return Result.error(e)

async def validate_deviantart(email: str) -> Result:
    return await _check(email)
