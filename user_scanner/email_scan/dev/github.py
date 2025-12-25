import asyncio
import httpx
import re

async def check_email(email):
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "referer": "https://github.com/signup"
    }

    async with httpx.AsyncClient(headers=headers, http2=True, follow_redirects=True) as client:
        res = await client.get("https://github.com/signup")

        token_match = re.search(r'name="authenticity_token" value="([^"]+)"', res.text)
        if not token_match:
            return "Token not found"

        token = token_match.group(1)

        data = {
            "authenticity_token": token,
            "value": email
        }

        post_headers = {"accept": "*/*", "x-requested-with": "XMLHttpRequest"}
        response = await client.post("https://github.com/email_validity_checks", data=data, headers=post_headers)

        if "The email you have provided is already associated with an account." not in response.text:
            return f"[+] {email} is not REGISTERED"
        else:
            return f"[-] {email} is Registerd"

async def main():
    email_to_test = input("Enter the email: ")
    result = await check_email(email_to_test)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())






