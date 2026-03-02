import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.accounts.firefox.com/v1/account/status"
    show_url = "https://firefox.com"

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.post(
                url,
                data={"email": email}
            )

            if "false" in response.text:
                return Result.available(url=show_url)

            if "true" in response.text:
                return Result.taken(url=show_url)

            return Result.error("Rate limited or unexpected response")

        except Exception as e:
            return Result.error(str(e))


async def validate_firefox(email: str) -> Result:
    return await _check(email)
