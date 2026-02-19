import httpx
import re
import time
import uuid
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://saashub.com"
    url = "https://www.saashub.com/register"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'accept-language': "en-US,en;q=0.9",
        'referer': "https://www.google.com/"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            r_get = await client.get(url, headers=headers)
            if r_get.status_code != 200:
                return Result.error(f"Failed to load register page: {r_get.status_code}")

            token_match = re.search(
                r'name="authenticity_token" value="([^"]+)"', r_get.text)
            if not token_match:
                return Result.error("Could not find authenticity_token in response")

            auth_token = token_match.group(1)

            payload = {
                'authenticity_token': auth_token,
                'user[email]': email,
                'user[username]': "t3rminalw0rri0r" + str(int(time.time()))[-4:],
                'user[password]': "",
                'user[password_confirmation]': "",
                'company_name': "",
                'commit': "Register"
            }

            post_headers = headers.copy()
            post_headers.update({
                'Accept': "text/vnd.turbo-stream.html, text/html, application/xhtml+xml",
                'origin': "https://www.saashub.com",
                'referer': url,
                'x-turbo-request-id': str(uuid.uuid4())
            })

            response = await client.post(url, data=payload, headers=post_headers)

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")

            res_text = response.text

            if "Email - has already been taken" in res_text:
                return Result.taken(url=show_url)

            elif "We couldn't sign you up" in res_text and "Email - has already been taken" not in res_text:
                return Result.available(url=show_url)

            else:
                return Result.error("Unexpected response body structure, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except Exception as e:
        return Result.error(e)


async def validate_saashub(email: str) -> Result:
    return await _check(email)
