import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://www.classmates.com"
    login_url = "https://www.classmates.com/auth/login"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'Origin': "https://www.classmates.com",
        'Referer': login_url,
        'Accept-Language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r_init = await client.get(login_url, headers=headers)

            if r_init.status_code == 403:
                return Result.error("Caught by WAF (403) during Handshake")

            csrf_match = re.search(
                r'name="_csrf" value="([^"]+)"', r_init.text)
            if not csrf_match:
                return Result.error("Failed to extract CSRF token from login page")

            csrf_token = csrf_match.group(1)

            payload = {
                '_csrf': csrf_token,
                'successUrl': "",
                'emailOrRegId': email,
                'password': "SafetyMismatch_123!",
                'rememberme': "no"
            }

            response = await client.post(login_url, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403) during Check")

            if response.status_code == 429:
                return Result.error("Rate limited by Classmates (429)")

            res_text = response.text

            if "invalid registration/password" in res_text:
                return Result.taken(url=show_url)

            if "did not find an account for the email address" in res_text:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_classmates(email: str) -> Result:
    return await _check(email)
