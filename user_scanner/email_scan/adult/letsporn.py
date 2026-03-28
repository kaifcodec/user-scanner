import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://letsporn.com"
    show_url = "https://letsporn.com"

    params = {
        'mode': "async",
        'function': "get_block",
        'block_id': "signup_signup_form_simple",
        'global': "true"
    }

    payload = {
        'format': "json",
        'mode': "async",
        'action': "signup",
        'email_link': "https://letsporn.com/email",
        'email': email,
        'username': email,
        'pass': "y0u_hav3_th3_s0wrd",
        'pass2': "but_n0t_th3_cr0wn"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'X-Requested-With': "XMLHttpRequest",
        'Origin': "https://letsporn.com",
        'Referer': "https://letsporn.com/categories/lesbian",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, params=params, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("403")
            
            data = response.json()
            errors = data.get("errors", [])
            
            for error in errors:
                if isinstance(error, dict):
                    code = error.get("code")
                    field = error.get("field")
                    if code == "exists" and field in ["username", "email"]:
                        return Result.taken(url=show_url)
                elif isinstance(error, str):
                    msg = error.lower()
                    if "already exists" in msg or "already in use" in msg:
                        return Result.taken(url=show_url)

            return Result.available(url=show_url)

    except Exception as e:
        return Result.error(e)

async def validate_letsporn(email: str) -> Result:
    return await _check(email)
