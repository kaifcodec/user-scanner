import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://huggingface.co/api/check-user-email"
    params = {'email': email}
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        'Accept-Encoding': "identity",
        'referer': "https://huggingface.co/join",
        'priority': "u=1, i"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=5)

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")

            if response.status_code == 400:
                data = response.json()
                if "already exists" in data.get("error", ""):
                    return Result.taken()

            if response.status_code == 200:
                return Result.available()

            return Result.error(f"HTTP Error: {response.status_code}")

        except Exception as e:
            return Result.error(e)


async def validate_huggingface(email: str) -> Result:
    return await _check(email)
