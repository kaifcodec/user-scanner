import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent

async def _check(email: str) -> Result:
    async with httpx.AsyncClient(http2=False, follow_redirects=True) as client:
        try:
            url = "https://stackoverflow.com/users/login"

            payload = {
                'ssrc': "login",
                'email': email,
                'password': "Password109-grt",
                'oauth_version': "",
                'oauth_server': ""
            }

            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                'Accept-Encoding': "identity",
                'sec-ch-ua-platform': '"Linux"',
                'origin': "https://stackoverflow.com",
                'referer': "https://stackoverflow.com/users/login"
            }

            response = await client.post(url, data=payload, headers=headers)
            body = response.text

            if "No user found with matching email" in body:
                return Result.available()
            elif "The email or password is incorrect" in body:
                return Result.taken()
            else:
                return Result.error("Unexpected response body")

        except Exception as e:
            return Result.error(f"unexpected exception: {e}")

async def validate_stackoverflow(email: str) -> Result:
    return await _check(email)
