import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    url = "https://www.babestation.tv/user/send/username-reminder"
    show_url = "https://babestation.tv"

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "application/json, text/plain, */*",
        'Content-Type': "application/json",
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://www.babestation.tv",
        'referer': "https://www.babestation.tv/forgot-password-or-username",
        'accept-language': "en-US,en;q=0.9",
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code in [200, 404]:
                data = response.json()
                success = data.get("success")

                if success is True:
                    return Result.taken(url=show_url)

                if success is False:
                    errors = data.get("errors", [])
                    if "Email not found" in errors:
                        return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}")


async def validate_babestation(email: str) -> Result:
    return await _check(email)
