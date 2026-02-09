import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    home_url = "https://letterboxd.com/sign-in/"
    register_url = "https://letterboxd.com/user/standalone/register.do"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'X-Requested-With': "XMLHttpRequest",
        'Origin': "https://letterboxd.com",
        'Referer': "https://letterboxd.com/register/standalone/",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            await client.get(home_url, headers={'User-Agent': headers['User-Agent']})
            csrf_token = client.cookies.get("com.xk72.webparts.csrf")

            if not csrf_token:
                return Result.error("Could not extract Letterboxd CSRF token")

            payload = {
                '__csrf': csrf_token,
                'token': "",
                'emailAddress': email,
                'username': "th3_t3erminal_w0rri0r",
                'password': "n3v3r_F3lt_softn3ss",
                'termsAndAge': "true",
                'g-recaptcha-response': "",
                'h-captcha-response': ""
            }

            response = await client.post(register_url, data=payload, headers=headers)
            data = response.json()

            messages = data.get("messages", [])
            error_fields = data.get("errorFields", [])

            is_taken = any(
                "already associated with an account" in msg for msg in messages)

            if is_taken or "emailAddress" in error_fields:
                return Result.taken()

            if "result" in data and not is_taken:
                return Result.available()

            return Result.error("Unexpected response structure")

    except Exception as e:
        return Result.error(e)


async def validate_letterboxd(email: str) -> Result:
    return await _check(email)
