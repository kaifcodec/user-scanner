import re
import httpx
from user_scanner.core.result import Result

# The public web app's bearer token, embedded in the homepage HTML.
API_TOKEN_RE = re.compile(r'"API_TOKEN":"([^"]+)"')
VALIDATE_URL = "https://www.tumblr.com/api/v2/register/account/validate"

# response codes returned by the account-validate endpoint. A deliberately
# short password means a free email always trips PASSWORD_TOO_SHORT (so no
# account is created), while a taken email trips USER_EXISTS first regardless.
USER_EXISTS = 2
PASSWORD_TOO_SHORT = 1030


async def _check(email: str) -> Result:
    show_url = "https://tumblr.com"
    async with httpx.AsyncClient(timeout=15.0, http2=True, follow_redirects=True) as client:
        try:
            headers = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                'Accept-Language': "en-US,en;q=0.9",
            }

            home = await client.get("https://www.tumblr.com/", headers=headers)
            token_match = API_TOKEN_RE.search(home.text)
            if not token_match:
                return Result.error("Token extraction failed, report it via GitHub issues")
            token = token_match.group(1)

            auth_headers = {**headers, 'Authorization': f"Bearer {token}"}
            radar = await client.get("https://www.tumblr.com/api/v2/radar", headers=auth_headers)
            csrf = radar.headers.get("X-Csrf")
            if not csrf:
                return Result.error("CSRF extraction failed, report it via GitHub issues")

            response = await client.post(
                VALIDATE_URL,
                json={'email': email, 'password': "x", 'tumblelog': "osintuserprobe"},
                headers={
                    **auth_headers,
                    'X-CSRF': csrf,
                    'Accept': "application/json",
                    'content-type': "application/json",
                    'origin': "https://www.tumblr.com",
                    'referer': "https://www.tumblr.com/register",
                },
            )

            data = response.json().get("response")
            code = data.get("code") if isinstance(data, dict) else None
            if code == USER_EXISTS:
                return Result.taken(url=show_url)
            elif code == PASSWORD_TOO_SHORT:
                return Result.available(url=show_url)
            else:
                return Result.error("Unexpected response, report it via GitHub issues")

        except Exception as e:
            return Result.error(f"unexpected exception: {e}")


async def validate_tumblr(email: str) -> Result:
    return await _check(email)
