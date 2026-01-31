import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Language': "en-US,en;q=0.9",
        'Referer': "https://leetcode.com/accounts/login/",
        'Origin': "https://leetcode.com",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            await client.get("https://leetcode.com/accounts/login/", headers=headers)
            csrf_token = client.cookies.get("csrftoken")

            if not csrf_token:
                return Result.error("CSRF token not found, possible rate-limit")

            headers.update({
                'x-requested-with': "XMLHttpRequest",
                'referer': "https://leetcode.com/accounts/password/reset/",
            })

            payload = {
                'next': 'undefined',
                'userName': '',
                'email': email,
                'csrfmiddlewaretoken': csrf_token
            }

            response = await client.post(
                "https://leetcode.com/accounts/password/reset/",
                headers=headers,
                data=payload
            )

            if response.status_code in [200, 400]:
                data = response.json()

                if data.get("location") == "/accounts/password/reset/done/":
                    return Result.taken()

                email_field = data.get("form", {}).get(
                    "fields", {}).get("email", {})
                errors = email_field.get("errors", [])

                if any("not assigned to any user account" in err for err in errors):
                    return Result.available()

                return Result.error("Unexpected response data")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(e)


async def validate_leetcode(email: str) -> Result:
    return await _check(email)
