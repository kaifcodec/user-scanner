import asyncio
import httpx

async def check_x(email):
    url = f"https://api.x.com/i/users/email_available.json?email={email}"
    headers = {
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "x-twitter-client-language": "en",
        "x-twitter-active-user": "yes",
        "referer": "https://x.com/"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            resp = await client.get(url, headers=headers)
            data = resp.json()
            if data.get("taken"):
                return f"[!] {email} -> REGISTERED"
            return f"[*] {email} -> NOT REGISTERED"
        except Exception as e:
            return f"Error checking {email}: {e}"

if __name__ == "__main__":
    target_email = input("Enter Email: ").strip()
    result = asyncio.run(check_x(target_email))
    print(result)
