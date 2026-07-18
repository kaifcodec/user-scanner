import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://v2.heyjapan.net/password/passwordCode"
    show_url = "https://heyjapan.net"

    payload = {
        "email": email
    }

    headers = {
        'User-Agent': "okhttp/5.3.2",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json"
    }

    async with httpx.AsyncClient(timeout=15.0, http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            data = response.json()
            message = data.get("message", "")

            if response.status_code == 200 and message == "Gửi mã khôi phục qua email thành công":
                return Result.taken(url=show_url)

            if response.status_code == 404 and message == "Email does not exist!":
                return Result.available(url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_heyjapan(email: str) -> Result:
    """
    HeyJapan email validator. Note: This will send a restore code via email if it exists.
    """
    return await _check(email)
