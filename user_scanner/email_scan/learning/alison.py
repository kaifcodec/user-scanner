import httpx
import re
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://alison.com/register"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        'Origin': "https://alison.com",
        'Referer': "https://alison.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=7.0, follow_redirects=True) as client:
            init_res = await client.get(url, headers=headers)

            token_match = re.search(r'name="_token"\s+value="([^"]+)"', init_res.text)
            if not token_match:
                return Result.error("Unable to extract CSRF token from Alison")

            csrf_token = token_match.group(1)

            payload = {
                '_token': csrf_token,
                'firstname': "The",
                'lastname': "SilentSowrd",
                'signup_email': email,
                'signup_password': "",
                'signup_tc_social': "1",
                'current': "https://alison.com",
                'route_name': "site.home"
            }

            response = await client.post(url, data=payload, headers=headers)
            body = response.text

            if "The signup email has already been taken" in body:
                return Result.taken()

            if 'id="emailNew"' in body and "The signup email has already been taken" not in body:
                return Result.available()

            return Result.error("Unexpected response body, report it on github")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out (Alison)")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Alison)")
    except Exception as e:
        return Result.error(e)

async def validate_alison(email: str) -> Result:
    return await _check(email)
