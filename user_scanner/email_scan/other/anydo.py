import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://sm-prod2.any.do/check_email"
    show_url = "https://any.do"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Accept-Language": "en,en-US;q=0.5",
        "Referer": "https://desktop.any.do/",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Platform": "3",
        "Origin": "https://desktop.any.do",
        "DNT": "1",
        "Connection": "keep-alive",
    }

    data = {"email": email}

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.post(url, json=data, headers=headers)

            if response.status_code == 200:
                json_data = response.json()

                if json_data.get("user_exists") is True:
                    return Result.taken(url=show_url)

                if json_data.get("user_exists") is False:
                    return Result.available(url=show_url)

            return Result.error("Rate limited or unexpected response")

        except Exception as e:
            return Result.error(str(e))


async def validate_anydo(email: str) -> Result:
    return await _check(email)
