import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Accept': '*/*',
        'Origin': 'https://accounts.zoho.com',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            await client.get("https://accounts.zoho.com/register", headers=headers)

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
                message = data.get("message")
                status = data.get("status_code")

                if message == "User exists" and status == 201:
                    return Result.taken()

                elif status == 400:
                    return Result.available()

                else:
                    return Result.error(data)

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))


async def validate_zoho(email: str) -> Result:
    return await _check(email)
