import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    headers = {
        'User-Agent': get_random_user_agent(),
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Accept': '*/*',
        'Origin': 'https://accounts.zoho.com',
        'Referer': 'https://accounts.zoho.com/',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            await client.get("https://accounts.zoho.com/signin", headers=headers)
            csrf_cookie = client.cookies.get("iamcsr")

            if not csrf_cookie:
                return Result.error("CSRF cookie not found")

            headers['X-ZCSRF-TOKEN'] = f'iamcsrcoo={csrf_cookie}'

            payload = {
                'mode': 'primary',
                'servicename': 'ZohoCRM',
                'serviceurl': 'https://crm.zoho.com/crm/ShowHomePage.do',
                'service_language': 'en'
            }

            response = await client.post(
                f'https://accounts.zoho.com/signin/v2/lookup/{email}',
                headers=headers,
                data=payload
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get("status_code")
                message = data.get("message", "")

                if status == 201 or message == "User exists":
                    return Result.taken()

                elif status == 400:
                    return Result.available()

                elif "User exists in another DC" in message:
                    return Result.taken()

                return Result.error("Unexpected response body, report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_zoho(email: str) -> Result:
    return await _check(email)
