import re

import httpx
from user_scanner.core.result import Result


def _check(user: str) -> Result:
    show_url = "https://facebook.com"

    if not (1 <= len(user) <= 50):
        return Result.error("Length must be 1-50 characters")

    if not re.match(r"^[a-zA-Z0-9.]+$", user):
        return Result.error("Only letters, numbers and periods allowed")

    if user.isdigit():
        return Result.error("Username cannot be numbers only")

    if user.startswith(".") or user.endswith("."):
        return Result.error("Username cannot start or end with a period")

    with httpx.Client(http2=True, follow_redirects=False, timeout=10.0) as client:
        try:
            headers1 = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                'Accept-Encoding': "identity",
                'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            }
            client.get("https://m.facebook.com/login/", headers=headers1)

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
            res = client.get("https://www.facebook.com", params={'_rdr': ""}, headers=headers2)
            html = res.text

            lsd_match = re.search(r'\["LSD",\[\],\{"token":".*?\}\]\}', html) or \
                re.search(r'name="lsd"\s+value="([^"]+)"', html) or \
                re.search(r'"lsd":"([^"]+)"', html)

            j_match = re.search(r'jazoest=(\d+)', html) or \
                re.search(r'name="jazoest"\s+value="(\d+)"', html)

            lsd = lsd_match.group(1) if lsd_match else None
            jazoest = j_match.group(1) if j_match else None

            if not lsd or not jazoest:
                return Result.error(f"Token extraction failed (LSD: {bool(lsd)}, Jazoest: {bool(jazoest)})")

            headers3 = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                'Accept-Encoding': "identity",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                'sec-ch-ua-mobile': "?0",
                'sec-ch-ua-platform': '"Linux"',
                'referer': "https://www.facebook.com",
                'x-ig-app-id': "936619743392459",
                'x-requested-with': "XMLHttpRequest",
                'accept-language': "en-US,en;q=0.9",
            }

            params = {
                'username': user,
                'fb_dtsg': lsd,
                'jazoest': jazoest,
            }

            res = client.get("https://www.facebook.com/ajax/username availability/", headers=headers3, params=params)
            
            if res.status_code == 200:
                return Result.success(show_url=show_url, reason=f"Username {user} is available")
            else:
                return Result.error(f"Unexpected status code: {res.status_code}")
                
        except httpx.TimeoutException:
            return Result.error("Request timed out")
        except Exception as e:
            return Result.error(f"Error: {str(e)}")
