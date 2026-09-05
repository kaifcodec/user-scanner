import httpx

from user_scanner.core.helpers import get_global_timeout, get_proxy
from user_scanner.core.result import Result

BASE_URL = "https://medal.tv"


async def validate_medal(email: str) -> Result:
    try:
        async with httpx.AsyncClient(
            timeout=get_global_timeout() or 15.0, proxy=get_proxy()
        ) as client:
            response = await client.post(
                f"{BASE_URL}/api/users/email",
                json={"email": email},
            )
    except httpx.HTTPError as exc:
        return Result.error(exc, url=f"{BASE_URL}/login")

    if response.status_code == 429:
        return Result.error("Rate limited by Medal", url=f"{BASE_URL}/login")
    if response.status_code != 200:
        return Result.error(
            f"Unexpected response status: {response.status_code}",
            url=f"{BASE_URL}/login",
        )

    try:
        data = response.json()
    except ValueError:
        return Result.error(
            "Medal returned a non-JSON email response", url=f"{BASE_URL}/login"
        )

    if data.get("valid") is not True:
        return Result.error("Medal rejected the email", url=f"{BASE_URL}/login")
    if data.get("exists") is True:
        return Result.taken(url=f"{BASE_URL}/login")
    if data.get("exists") is False:
        return Result.available(url=f"{BASE_URL}/login")
    return Result.error("Unexpected Medal email response", url=f"{BASE_URL}/login")
