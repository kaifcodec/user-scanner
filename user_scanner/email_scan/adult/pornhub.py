import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    base_url = "https://www.pornhub.com"
    show_url = "https://pornhub.com"
    check_api = f"{base_url}/api/v1/user/create_account_check"

    headers = {
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "origin": base_url,
        "referer": base_url + "/",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
    }

    async with httpx.AsyncClient(http2=True, follow_redirects=True, timeout=5.0) as client:
        try:
            landing_resp = await client.get(base_url, headers=headers)
            token_match = re.search(
                r'var\s+token\s*=\s*"([^"]+)"', landing_resp.text)

            if not token_match:
                return Result.error("Failed to extract dynamic token from HTML")

            token = token_match.group(1)

            params = {"token": token}
            payload = {
                "check_what": "email",
                "email": email
            }

            response = await client.post(
                check_api,
                params=params,
                headers=headers,
                data=payload
            )

            if response.status_code == 429:
                return Result.error("Rate limited, wait for a few minutes")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()
            status = data.get("email")
            error_msg = data.get("error_message", "")
            email_dom = email.split("@")[-1]

            if status == "create_account_failed":
                if "Email extension" in error_msg:
                    return Result.available(url=show_url, reason=f"Domain '{email_dom}' is not allowed by PornHub")
                if "delivery issues" in error_msg:
                    return Result.error(url=show_url, reason="The email is experiencing email delivery issues")

            if status == "create_account_passed":
                return Result.available(url=show_url)
            elif "already in use" in error_msg.lower() or "already registered" in error_msg:
                return Result.taken(url=show_url)
            else:
                return Result.error(f"Unexpected API response: {status}: {error_msg}")

        except Exception as e:
            return Result.error(e)


async def validate_pornhub(email: str) -> Result:
    return await _check(email)
