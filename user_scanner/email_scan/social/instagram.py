import httpx
from user_scanner.core.result import Result


async def _check(email):
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    async with httpx.AsyncClient(headers={"user-agent": USER_AGENT}, http2=True) as client:
        await client.get("https://www.instagram.com/")
        csrf = client.cookies.get("csrftoken")

        headers = {
            "x-csrftoken": csrf,
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            'Accept-Encoding': "identity",
            'sec-ch-ua-full-version-list': "\"Google Chrome\";v=\"143.0.7499.146\", \"Chromium\";v=\"143.0.7499.146\", \"Not A(Brand\";v=\"24.0.0.0\"",
            'sec-ch-ua-platform': "\"Linux\"",
            'sec-ch-ua': "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
            'sec-ch-ua-model': "\"\"",
            'sec-ch-ua-mobile': "?0",
            'x-ig-app-id': "936619743392459",
            'x-requested-with': "XMLHttpRequest",
            'x-instagram-ajax': "1031566424",
            'x-asbd-id': "359341",
            'x-ig-www-claim': "0",
            'sec-ch-ua-platform-version': "\"\"",
            'origin': "https://www.instagram.com",
            'referer': "https://www.instagram.com/accounts/password/reset/"
        }

        response = await client.post(
            "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
            data={"email_or_username": email},
            headers=headers
        )

        data = response.json()
        status_val = data.get("status")
        if status_val == "ok":
            return Result.taken()
        elif status_val == "fail":
            return Result.available()
        else:
            return Result.error("Unexpected response body, report it on github")



async def validate_instagram(email: str) -> Result:
    return await _check(email)
