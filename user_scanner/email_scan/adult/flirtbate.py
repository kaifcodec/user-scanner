import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent

async def _check(email: str) -> Result:
    url = "https://api.flirtbate.com/api/v1/customer/reset-password-email"

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "application/json",
        'Content-Type': "application/json",
        'origin': "https://flirtbate.com",
        'referer': "https://flirtbate.com/",
        'accept-language': "en-US,en;q=0.9",
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited (429)")

            data = response.json()
            message = data.get("message", "")

            if "Reset password email sent" in message:
                return Result.taken()

            if "Email invalid for reset password" in message:
                return Result.available()

            return Result.error("Unexpected response body, report it via GitHub issues")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")

async def validate_flirtbate(email: str) -> Result:
    return await _check(email)
