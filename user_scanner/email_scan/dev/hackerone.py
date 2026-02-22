import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://hackerone.com"
    signup_url = "https://hackerone.com/sign_up"
    api_url = "https://hackerone.com/users"

    headers_init = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Encoding': "identity",
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-full-version': '"145.0.7632.109"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-platform': '"Linux"',
        'sec-ch-ua-platform-version': '""',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version-list': '"Not:A-Brand";v="99.0.0.0", "Google Chrome";v="145.0.7632.109", "Chromium";v="145.0.7632.109"',
        'upgrade-insecure-requests': "1",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "navigate",
        'sec-fetch-user': "?1",
        'sec-fetch-dest': "document",
        'referer': "https://hackerone.com/users/sign_in",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=0, i"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r_page = await client.get(signup_url, headers=headers_init)

            if r_page.status_code == 403:
                return Result.error("Caught by WAF (403) during Handshake")

            csrf_match = re.search(
                r'name="csrf-token" content="([^"]+)"', r_page.text)
            if not csrf_match:
                return Result.error("Failed to extract CSRF token")

            csrf_token = csrf_match.group(1)

            reg_headers = {
                'sec-ch-ua-full-version-list': '"Not:A-Brand";v="99.0.0.0", "Google Chrome";v="145.0.7632.109", "Chromium";v="145.0.7632.109"',
                'sec-ch-ua-platform': '"Linux"',
                'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
                'sec-ch-ua-bitness': '"64"',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-mobile': "?0",
                'sec-ch-ua-arch': '"x86"',
                'x-requested-with': "XMLHttpRequest",
                'sec-ch-ua-full-version': '"145.0.7632.109"',
                'accept': "application/json, text/javascript, */*; q=0.01",
                'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
                'x-csrf-token': csrf_token,
                'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                'sec-ch-ua-platform-version': '""',
                'origin': "https://hackerone.com",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://hackerone.com/users/sign_up",
                'accept-encoding': "identity",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=1, i"
            }

            payload = {
                'user[name]': "St33l_h3art_g3t_n0_l0v3",
                'user[username]': "kn0wl3dg3_is_curs3",
                'user[email]': email,
                'user[password]': "thisw0rldwasn3v3rg00d",
                'user[password_confirmation]': "mismatch_on_purpose"
            }

            response = await client.post(api_url, data=payload, headers=reg_headers)
            status = response.status_code

            if status == 403:
                return Result.error("Caught by WAF (403) during Validation")

            data = response.json()
            errors = data.get("errors", {})

            if "has already been taken" in str(errors.get("email", [])):
                return Result.taken(url=show_url)

            if "email" not in errors:
                return Result.available(url=show_url)

            if status == 429:
                return Result.error("Rate limited by HackerOne")

            return Result.error(f"Unexpected response: {status}")

    except Exception as e:
        return Result.error(e)


async def validate_hackerone(email: str) -> Result:
    return await _check(email)
