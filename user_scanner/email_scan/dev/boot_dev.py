import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:

    show_url = "https://boot.dev"
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
        'Referer': 'https://boot.dev/',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            response = await client.post(
                "https://api.boot.dev/v1/users/email/exists",
                headers=headers,
                json={"email": email}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("Exists") is True:
                    return Result.taken(url=show_url)
                else:
                    return Result.available(url=show_url)

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(e)


async def validate_boot(email: str) -> Result:
    return await _check(email)