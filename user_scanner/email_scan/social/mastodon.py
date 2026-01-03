import httpx
import re
from user_scanner.core.result import Result


async def _check(email):
    base_url = "https://mastodon.social"
    signup_url = f"{base_url}/auth/sign_up"
    post_url = f"{base_url}/auth"

    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "referer": "https://mastodon.social/explore",
        "origin": "https://mastodon.social"
    }

    async with httpx.AsyncClient(http2=True, headers=headers, follow_redirects=True) as client:
        try:
            initial_resp = await client.get(signup_url)
            if initial_resp.status_code != 200:
                return Result.error(f"Failed to access signup page: {initial_resp.status_code}")

            token_match = re.search(
                r'name="csrf-token" content="([^"]+)"', initial_resp.text)
            if not token_match:
                return Result.error("Could not find authenticity token")

            csrf_token = token_match.group(1)

            payload = {
                "authenticity_token": csrf_token,
                "user[account_attributes][username]": "no3motions_robot_020102",
                "user[email]": email,
                "user[password]": "Theleftalone@me",
                "user[password_confirmation]": "Theleftalone@me",
                "user[agreement]": "1",
                "button": ""
            }

            response = await client.post(post_url, data=payload)

            if "has already been taken" in response.text:
                return Result.taken()
            else:
                return Result.available()

        except Exception as e:
            return Result.error(e)


def validate_mastodon(email: str) -> Result:
    return _check(email)
