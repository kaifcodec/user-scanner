import re
import httpx
from user_scanner.core.result import Result

SIGNUP_URL = "https://disqus.com/profile/signup/"
# Django surfaces this field error before the reCAPTCHA check, so an
# unauthenticated POST with a deliberately blank password (which always fails
# validation, so no account is ever created) still reveals whether the email
# is taken.
EMAIL_TAKEN_MARKER = "The e-mail address you specified is already in use"


async def _check(email: str) -> Result:
    show_url = "https://disqus.com"
    async with httpx.AsyncClient(timeout=15.0, http2=True, follow_redirects=True) as client:
        try:
            headers = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                'Accept-Language': "en-US,en;q=0.9",
                'origin': "https://disqus.com",
                'referer': SIGNUP_URL,
            }

            page = await client.get(SIGNUP_URL, headers=headers)
            match = re.search(r'name=[\'"]csrfmiddlewaretoken[\'"]\s+value=[\'"]([^\'"]+)[\'"]', page.text)
            token = match.group(1) if match else client.cookies.get("csrftoken")
            if not token:
                return Result.error("Token extraction failed, report it via GitHub issues")

            payload = {
                'csrfmiddlewaretoken': token,
                'display_name': "osintuser",
                'email': email,
                'password': "",
                'tos': "on",
                'privacy-policy': "on",
                'age-declaration': "on",
                'data-sharing': "on",
            }
            response = await client.post(
                SIGNUP_URL,
                data=payload,
                headers={**headers, 'content-type': "application/x-www-form-urlencoded"},
            )
            body = response.text

            if EMAIL_TAKEN_MARKER in body:
                return Result.taken(url=show_url)
            elif "errorlist" in body:
                return Result.available(url=show_url)
            else:
                return Result.error("Unexpected response, report it via GitHub issues")

        except Exception as e:
            return Result.error(f"unexpected exception: {e}")


async def validate_disqus(email: str) -> Result:
    return await _check(email)
