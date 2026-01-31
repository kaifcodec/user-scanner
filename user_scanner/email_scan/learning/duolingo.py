import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    headers = {
        'authority': 'www.duolingo.com',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
        'Referer': 'https://www.duolingo.com/',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            response = await client.get(
                f"https://www.duolingo.com/2017-06-30/users?email={email}",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                # Duolingo returns a list of users matching the email
                if data.get("users") and len(data["users"]) > 0:
                    return Result.taken()
                else:
                    return Result.available()
            
            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(e)

async def validate_duolingo(email: str) -> Result:
    return await _check(email)
