import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.screener.in/register/"
    show_url = "https://www.screener.in"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Language': "en-US,en;q=0.5",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Brave";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': "?1",
        'Upgrade-Insecure-Requests': "1",
    }

    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            init_res = await client.get(url, headers=headers)

            if init_res.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")
            if init_res.status_code == 429:
                return Result.error("Rate limited by Screener (429)")
            if init_res.status_code != 200:
                return Result.error(f"HTTP Error: {init_res.status_code}")

            csrf_middleware = re.search(
                r'name="csrfmiddlewaretoken" value="([^"]+)"', init_res.text)
            reg_token = re.search(
                r'name="token" value="([^"]+)"', init_res.text)

            if not csrf_middleware or not reg_token:
                return Result.error("Unexpected response body structure, report it via GitHub issues")

            payload = {
                'csrfmiddlewaretoken': csrf_middleware.group(1),
                'next': "",
                'token': reg_token.group(1),
                'email': email,
                'email2': email,
                'password': ""
            }

            api_headers = headers.copy()
            api_headers.update({
                'Origin': "https://www.screener.in",
                'Referer': url,
            })

            response = await client.post(url, data=payload, headers=api_headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF or IP Block (403)")
            if response.status_code == 429:
                return Result.error("Rate limited by Screener (429)")
            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            res_text = response.text

            if "User account with this Email already exists" in res_text:
                return Result.taken(url=show_url)

            if '<ul class="errorlist"><li>This field is required.</li>' in res_text:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_screener(email: str) -> Result:
    return await _check(email)
