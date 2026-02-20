import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://facebook.com"
    async with httpx.AsyncClient(http2=True, follow_redirects=False) as client:
        try:
            url1 = "https://m.facebook.com/login/"
            headers1 = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                'Accept-Encoding': "identity",
                'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            }
            await client.get(url1, headers=headers1)

            url2 = "https://www.facebook.com"
            params2 = {'_rdr': ""}
            headers2 = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                'Accept-Encoding': "identity",
                'upgrade-insecure-requests': "1",
                'sec-fetch-site': "cross-site",
                'sec-fetch-mode': "navigate",
                'sec-fetch-user': "?1",
                'sec-fetch-dest': "document",
                'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                'sec-ch-ua-mobile': "?0",
                'sec-ch-ua-platform': '"Linux"',
                'referer': "https://www.google.com/",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=0, i"
            }
            res2 = await client.get(url2, params=params2, headers=headers2)

            html = res2.text

            # Try to find LSD New JSON format first, then old HTML format
            lsd_match = re.search(r'\["LSD",\[\],\{"token":"([^"]+)"\}', html) or \
                re.search(r'name="lsd"\s+value="([^"]+)"', html) or \
                re.search(r'"lsd":"([^"]+)"', html)

            # Try to find jazoest URL param first, then hidden input
            j_match = re.search(r'jazoest=(\d+)', html) or \
                re.search(r'name="jazoest"\s+value="(\d+)"', html)

            lsd = lsd_match.group(1) if lsd_match else None
            jazoest = j_match.group(1) if j_match else None

            # see which one is missing
            if not lsd or not jazoest:
                return Result.error(f"Token extraction failed (LSD: {bool(lsd)}, Jazoest: {bool(jazoest)})")

            if not j_match or not lsd_match:
                return Result.error("Failed to extract tokens (LSD/Jazoest)")

            url3 = "https://www.facebook.com/ajax/login/help/identify.php"
            params3 = {'ctx': "recover"}

            payload3 = {
                'jazoest': jazoest,
                'lsd': lsd,
                'email': email,
                'did_submit': "1",
                '__user': "0",
                '__a': "1",
                '__req': "7"
            }

            headers3 = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                'Accept-Encoding': "identity",
                'sec-ch-ua-full-version-list': '"Google Chrome";v="143.0.7499.192", "Chromium";v="143.0.7499.192", "Not A(Brand";v="24.0.0.0"',
                'sec-ch-ua-platform': '"Linux"',
                'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-mobile': "?0",
                'x-asbd-id': "359341",
                'x-fb-lsd': lsd,
                'sec-ch-prefers-color-scheme': "dark",
                'sec-ch-ua-platform-version': '""',
                'origin': "https://www.facebook.com",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://www.facebook.com/login/identify/?ctx=recover&ars=facebook_login&from_login_screen=0",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=1, i"
            }

            response = await client.post(url3, params=params3, data=payload3, headers=headers3)
            body = response.text

            if "redirectPageTo" in body and "ServerRedirect" in body:
                return Result.taken(url=show_url)
            elif "No search results" in body or "Your search did not return any results." in body:
                return Result.available(url=show_url)
            else:
                return Result.error("Unexpected error, report it via GitHub issues")

        except Exception as e:
            return Result.error(f"Unexpected exception: {e}")


async def validate_facebook(email: str) -> Result:
    return await _check(email)
