import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    headers = {
        'authority': 'axonaut.com',
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'referer': 'https://axonaut.com/en',
        'accept-language': 'en-US,en;q=0.9',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            response = await client.get(
                f'https://axonaut.com/onboarding/?email={email}',
                headers=headers
            )

            if response.status_code == 302 and "/login?email" in response.headers.get('Location', ''):

                return Result.taken()

            elif response.status_code == 200:
                return Result.available()

            else:
                return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))


async def validate_axonaut(email: str) -> Result:
    return await _check(email)
