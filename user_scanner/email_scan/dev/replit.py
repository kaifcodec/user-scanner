import httpx
import re
from user_scanner.core.result import Result

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


async def _check(email: str) -> Result:
    """
    Performs Replit email existence check via signup API.

    Returns:
        Result.available() if email not registered
        Result.taken() if email already exists
        Result.error(msg) on failure
    """
    signup_url = "https://replit.com/signup"
    check_url = "https://replit.com/data/user/exists"

    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://replit.com",
        "referer": "https://replit.com/signup",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "x-requested-with": "XMLHttpRequest",
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
        try:
            # Step 1: hit signup page to establish cookies
            await client.get(signup_url)

            # Step 2: call email existence endpoint
            payload = {"email": email}
            resp = await client.post(check_url, json=payload, headers=headers)

            if resp.status_code == 403:
                return Result.error("Replit blocks automated requests (403)")


            data = resp.json()

            # Expected response: { "exists": true/false }
            exists = data.get("exists")

            if exists is True:
                return Result.taken()

            if exists is False:
                return Result.available()

            return Result.error("Unexpected response format")

        except Exception as e:
            return Result.error(str(e))


async def validate_replit(email: str) -> Result:
    """
    Public validator for Replit email existence.
    """
    if not EMAIL_RE.match(email):
        return Result.error("Invalid email format")

    return await _check(email)
