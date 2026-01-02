import httpx
from user_scanner.core.result import Result

async def _check(email):
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    async with httpx.AsyncClient(headers={"user-agent": USER_AGENT}, http2=True) as client:
        await client.get("https://www.instagram.com/")
        csrf = client.cookies.get("csrftoken")

        headers = {
            "x-csrftoken": csrf,
            "x-ig-app-id": "936619743392459",
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://www.instagram.com/accounts/password/reset/"
        }

        response = await client.post(
            "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
            data={"email_or_username": email},
            headers=headers
        )

        data = response.json()
        return Result.taken() if data.get("status") == "ok" else Result.available()

def validate_instagram(email: str) -> Result:
    return _check(email)
