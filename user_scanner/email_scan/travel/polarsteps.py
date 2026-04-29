iimport httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.polarsteps.com/validation/unique"
    show_url = "https://polarsteps.com"

    payload = {
        'field': "users.email",
        'value': email
    }

    headers = {
        'User-Agent': "Polarsteps/8.0.0 (com.polarsteps; build:2000006379; Android 10)",
        'Accept-Encoding': "identity",
        'polarsteps-api-version': "55",
        'polarsteps-user-language': "en-US",
        'polarsteps-device-id': "a1b2c3d4e5f6g7h8",
        'polarsteps-device-name': "Samsung%20SM-G973F",
        'polarsteps-device-platform': "1",
        'Accept-Language': "en-US"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("403")

            res_text = response.text.strip().upper()

            if res_text == "OK":
                return Result.available(url=show_url)

            if res_text == "INVALID":
                return Result.taken(url=show_url)

            return Result.error(f"Unexpected: {res_text[:10]}")

    except Exception as e:
        return Result.error(e)


async def validate_polarsteps(email: str) -> Result:
    return await _check(email)
