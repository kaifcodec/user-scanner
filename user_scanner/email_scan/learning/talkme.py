import hashlib

import httpx

from user_scanner.core.result import Result


async def validate_talkme(email: str) -> Result:
    """Check TalkMe's login endpoint without sending email."""
    show_url = "https://www.talkme.ai"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.talkme.ai/api/user/login",
                json={
                    "email": email,
                    "password": hashlib.md5(
                        b"scanner-invalid-password", usedforsecurity=False
                    ).hexdigest(),
                },
            )

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)
            if response.status_code != 200:
                return Result.error(
                    f"Unexpected response status: {response.status_code}",
                    url=show_url,
                )

            data = response.json()
            if data.get("errCode") == 80820021:
                return Result.available(url=show_url)
            if data.get("errCode") == 80820053:
                return Result.taken(url=show_url)
            return Result.error("Unexpected response body", url=show_url)
    except (httpx.HTTPError, ValueError) as exc:
        return Result.error(exc, url=show_url)
