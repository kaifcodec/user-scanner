import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.plurk.com/Users/isEmailFound"
    show_url = "https://www.plurk.com"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.plurk.com",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers=headers,
                data={"email": email}
            )

        if response.status_code == 403:
            return Result.error("Caught by WAF or IP Block (403)")

        if response.status_code == 429:
            return Result.error("Rate limited (429)")

        if response.status_code != 200:
            return Result.error(f"HTTP Error: {response.status_code}")

        text = response.text.strip()

        if text == "True":
            return Result.taken(url=show_url)

        if text == "False":
            return Result.available(url=show_url)

        return Result.error("Unexpected response body structure")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out")

    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond")

    except Exception as e:
        return Result.error(e)


async def validate_plurk(email: str) -> Result:
    return await _check(email)
