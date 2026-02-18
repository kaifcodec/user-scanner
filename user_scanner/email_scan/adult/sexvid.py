import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent

async def _check(email: str) -> Result:
    show_url = "https://sexvid.pro"
    url = "https://www.sexvid.pro/reset-password/"

    payload = {
        'action': "restore_password",
        'mode': "async",
        'format': "json",
        'email_link': "https://www.sexvid.pro/signup.php",
        'email': email,
        'code': "xxxxx"
    }

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "*/*",
        'X-Requested-With': "XMLHttpRequest",
        'Origin': "https://www.sexvid.pro",
        'Referer': "https://www.sexvid.pro/reset-password/",
        'Content-Type': "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient(http2=False, timeout=5.0) as client:
        try:
            response = await client.post(url, data=payload, headers=headers)
            res_text = response.text

            if "doesnt_exist" in res_text or "No user with such email exists" in res_text:
                return Result.available(url=show_url)
            elif "A new generated password has been sent" in res_text or "status\":\"success" in res_text:
                return Result.taken(url=show_url)
            elif response.status_code == 429:
                return Result.error("Rate-limited")
            else:
                return Result.error(f"[{response.status_code}] Unexpected response body, report it via GitHub issues")

        except Exception as e:
            return Result.error(e)

async def validate_sexvid(email: str) -> Result:
    return await _check(email)
