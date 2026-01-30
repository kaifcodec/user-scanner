import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': '*/*',
        'Accept-Language': 'fr,fr-FR;q=0.9,en;q=0.8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.naturabuy.fr',
        'Referer': 'https://www.naturabuy.fr/register.php',
    }

    files = {
        'jsref': (None, 'email'),
        'jsvalue': (None, email),
        'registerMode': (None, 'full')
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                'https://www.naturabuy.fr/includes/ajax/register.php',
                headers=headers,
                files=files
            )

            if response.status_code != 200:
                return Result.error(f"Unexpected status: {response.status_code}")

            data = response.json()
            
            if data.get("free") is False:
                return Result.taken()
            elif data.get("free") is True:
                return Result.available()
            
            return Result.error("Unexpected response format")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(str(e))

async def validate_naturabuy(email: str) -> Result:
    return await _check(email)
