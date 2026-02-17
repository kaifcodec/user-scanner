import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://instagram"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"

    try:
        async with httpx.AsyncClient(headers={"user-agent": user_agent}, http2=True, timeout=15.0) as client:
            res = await client.get("https://www.instagram.com/accounts/password/reset/", follow_redirects=True)

            csrf = client.cookies.get("csrftoken")
            if not csrf:
                match = re.search(
                    r'["\']csrf_token["\']\s*:\s*["\']([^"\']+)["\']', res.text)
                if match:
                    csrf = match.group(1)

            if not csrf:
                return Result.error("CSRF token not found (IP may be flagged)")

            headers = {
                "x-csrftoken": csrf,
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "x-asbd-id": "359341",
                "origin": "https://www.instagram.com",
                "referer": "https://www.instagram.com/accounts/password/reset/",
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded"
            }

            response = await client.post(
                "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
                data={"email_or_username": email},
                headers=headers
            )

            if response.status_code in [200, 400]:
                data = response.json()
                status_val = data.get("status")

                if status_val == "ok":
                    return Result.taken(url=show_url)
                elif status_val == "fail":
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues")

            if response.status_code == 429:
                return Result.error("Rate limited (429)")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_instagram(email: str) -> Result:
    return await _check(email)
