import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://qiita.com"
    privacy_url = "https://qiita.com/privacy"
    signup_url = "https://qiita.com/signup?callback_action=login_or_signup&redirect_to=%2F&realm=qiita"
    reg_url = "https://qiita.com/registration"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': "?1",
        'origin': "https://qiita.com",
        'referer': signup_url,
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:

            await client.get(privacy_url, headers=headers)

            r_signup = await client.get(signup_url, headers=headers)
            csrf_match = re.search(
                r'name="csrf-token" content="([^"]+)"', r_signup.text)
            if not csrf_match:
                return Result.error("Failed to extract CSRF token")

            csrf_token = csrf_match.group(1)

            payload = {
                'authenticity_token': csrf_token,
                'user[url_name]': "scanner_check_99",
                'user[email]': email,
                'user[password]': "SafetyMismatch_123!",
                'g-recaptcha-response': "",
                'commit': "register",
                'redirect_to': "/"
            }

            response = await client.post(reg_url, data=payload, headers=headers)

            if "has already been taken" in response.text:
                return Result.taken(url=show_url)

            if "Email" in response.text and email in response.text:

                return Result.available(url=show_url)

            return Result.available(url=show_url)

    except Exception as e:
        return Result.error(e)


async def validate_qiita(email: str) -> Result:
    return await _check(email)
