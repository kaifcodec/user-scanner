import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    async with httpx.AsyncClient(http2=True, follow_redirects=True) as client:
        try:
            url1 = "https://github.com/signup"
            headers1 = {
                'host': 'github.com',
                'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'sec-fetch-site': 'cross-site',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'referer': 'https://www.google.com/',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'accept-language': 'en-US,en;q=0.9',
                'priority': 'u=0, i'
            }

            res1 = await client.get(url1, headers=headers1)
            html = res1.text

            csrf_match = re.search(r'data-csrf="true"\s+value="([^"]+)"', html)

            if not csrf_match:
                return Result.error("Failed to extract GitHub authenticity_token")

            csrf_token = csrf_match.group(1)

            url2 = "https://github.com/email_validity_checks"
            payload = {
                'authenticity_token': csrf_token,
                'value': email
            }

            headers2 = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                'Accept-Encoding': "gzip, deflate, br, zstd",
                'sec-ch-ua-platform': '"Linux"',
                'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
                'sec-ch-ua-mobile': "?0",
                'origin': "https://github.com",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://github.com/signup",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=1, i"
            }

            response = await client.post(url2, data=payload, headers=headers2)
            body = response.text

            if "already associated with an account" in body:
                return Result.taken()
            elif response.status_code == 200 and "Email is available" in body:
                return Result.available()
            else:
                return Result.error(f"Unexpected status code: {response.status_code}, report this via GitHub issues")

        except Exception as e:
            return Result.error(f"unexpected exception: {e}")


async def validate_github(email: str) -> Result:
    return await _check(email)
