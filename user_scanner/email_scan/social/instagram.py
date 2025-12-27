import asyncio
import httpx

async def check_instagram(email):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    async with httpx.AsyncClient(headers={"user-agent": ua}, http2=True) as client:
        await client.get("https://www.instagram.com/")
        csrf = client.cookies.get("csrftoken")

        headers = {
            "x-csrftoken": csrf,
            "x-ig-app-id": "936619743392459",
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://www.instagram.com/accounts/password/reset/"
        }

        resp = await client.post(
            "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
            data={"email_or_username": email},
            headers=headers
        )

        data = resp.json()
        if data.get("status") == "ok":
            return f"[!] {email} -> USED (Account exists)"
        return f"[*] {email} -> NOT USED"

if __name__ == "__main__":
    target = input("Enter the Email: ")
    print(asyncio.run(check_instagram(target)))










