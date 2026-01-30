import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    async with httpx.AsyncClient(http2=True) as client:
        try:
            url = "https://id.atlassian.com/rest/marketing-consent/config"
            payload = {"email": email}
            headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
                'Content-Type': "application/json",
                'Origin': "https://id.atlassian.com",
                'Referer': f"https://id.atlassian.com/login?email={email}"
            }

            response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                return Result.error(f"Status {response.status_code}")

            data = response.json()
            is_reg = data.get("implicitConsent")
            if is_reg is True:
                return Result.available()
            elif is_reg is False:
                return Result.taken()
            else:
                return Result.error(f"Unexpected error occured [{response.status_code}]")
        except Exception as e:
            return Result.error(f"Unexpected exception:{e}")


async def validate_bitbucket(email: str) -> Result:
    return await _check(email)
