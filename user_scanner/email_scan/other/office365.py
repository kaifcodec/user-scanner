import httpx
import random
import string
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    base_url = "https://outlook.office365.com/autodiscover/autodiscover.json/v1.0"
    show_url = "https://office365.com"

    headers = {
        "User-Agent": "Microsoft Office/16.0 (Windows NT 10.0; Microsoft Outlook 16.0.12026; Pro)",
        "Accept": "application/json",
    }

    def get_random_string(length: int) -> str:
        return "".join(random.choice(string.digits) for _ in range(length))

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:

            r = await client.get(
                f"{base_url}/{email}?Protocol=Autodiscoverv1",
                headers=headers,
            )

        if r.status_code == 403:
            return Result.error("Caught by WAF or IP Block (403)")

        if r.status_code == 429:
            return Result.error("Rate limited (429)")

        if r.status_code == 200:
            return Result.taken(url=show_url)

        return Result.available(url=show_url)

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out")

    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond")

    except Exception as e:
        return Result.error(e)


async def validate_office365(email: str) -> Result:
    return await _check(email)
