import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://motherless.xxx"
    url = "https://motherless.xxx/register/checkemail"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": show_url,
        "Referer": show_url + "/register",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    try:
        async with httpx.AsyncClient(http2=True, timeout=15.0) as client:
            response = await client.post(url, data={"email": email}, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited, wait for a few minutes")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            body = response.text

            # The field check reuses "not-available" for both existing accounts
            # and rejected input (e.g. "Invalid Host.").
            if 'class="not-available"' in body:
                if "invalid" in body.lower():
                    return Result.error("Email address rejected by Motherless")
                return Result.taken(url=show_url)

            if 'class="available"' in body:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body, report it via GitHub issues")

    except Exception as e:
        return Result.error(e)


async def validate_motherless(email: str) -> Result:
    return await _check(email)
