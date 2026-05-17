import httpx
import re
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://girlslife.com/register/"
    show_url = "https://girlslife.com/register/"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Encoding': "identity",
        'sec-ch-ua': '"Brave";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': "?1",
        'sec-ch-ua-platform': '"Android"',
        'sec-gpc': "1",
        'upgrade-insecure-requests': "1",
        'accept-language': "en-US,en;q=0.9",
        'origin': "https://girlslife.com",
        'referer': show_url,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # GET the page to extract the required _wpnonce
            init_res = await client.get(url, headers=headers)
            if init_res.status_code != 200:
                return Result.error(f"Failed to load register page: {init_res.status_code}")

            nonce_match = re.search(r'name="_wpnonce" value="([^"]+)"', init_res.text)

            if not nonce_match:
                return Result.error("Failed to parse response")

            nonce = nonce_match.group(1)

            # POST the validation payload
            payload = {
                'user_email-291233': email,
                'user_password-291233': "",
                'confirm_user_password-291233': "",
                'birth_date-291233': "",
                'streetaddress-291233': "Miami-1",
                'zip_code-291233': "6281",
                'form_id': "291233",
                'um_request': "",
                '_wpnonce': nonce,
                '_wp_http_referer': "/register/"
            }

            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by Cloudflare/WAF (403)")

            response_text = response.text

            if "Password is required" in response_text and 'The email you entered is incorrect' not in response_text:
                return Result.available(url=show_url)

            if 'The email you entered is incorrect' in response_text:
                return Result.taken(url=show_url)

            return Result.error("Unexpected response pattern")

    except Exception as e:
        return Result.error(str(e))

async def validate_girlslife(email: str) -> Result:
    return await _check(email)
