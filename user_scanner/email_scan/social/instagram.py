import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://instagram.com"
    user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"

    try:
        async with httpx.AsyncClient(
            headers={"user-agent": user_agent}, http2=True, timeout=10.0
        ) as client:
            res = await client.get("https://www.instagram.com/", follow_redirects=True)

            csrf = client.cookies.get("csrftoken")
            if not csrf:
                match = re.search(
                    r'["\']csrf_token["\']\s*:\s*["\']([^"\']+)["\']', res.text
                )
                if match:
                    csrf = match.group(1)

            if not csrf:
                return Result.error("CSRF token not found (IP may be flagged)")

            headers = {
                "x-csrftoken": csrf,
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "origin": "https://www.instagram.com",
                "referer": "https://www.instagram.com/",
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded",
            }

            response = await client.post(
                "https://www.instagram.com/api/v1/users/check_email/",
                data={"email": email, "sign_up_code": ""},
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("error_type") == "email_is_taken":
                    return Result.taken(url=show_url)
                elif data.get("available") is True:
                    return Result.available(url=show_url)

                return Result.error(
                    "Unexpected 200 response body, report it via GitHub issues"
                )

            if response.status_code == 400:
                data = response.json()
                if data.get("spam") is True:
                    # Instagram often blocks enumeration of non-existing emails with 'spam': true
                    return Result.available(url=show_url)

                return Result.error("Unexpected 400 response body")

            if response.status_code == 429:
                return Result.error("Rate limited (429)")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_instagram(email: str) -> Result:
    return await _check(email)
