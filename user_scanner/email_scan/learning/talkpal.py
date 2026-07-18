import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.talkpal.ai/api/v1/auth/recovery-request"
    show_url = "https://talkpal.ai"

    payload = {
        "email": email,
        "source": "app"
    }

    headers = {
        'User-Agent': "NitroFetch/1.0",
        'Accept': "application/json, text/plain, */*",
        'Content-Type': "application/json",
        'source': "app",
        'source-device': "ANDROID",
        'priority': "u=1, i"
    }

    async with httpx.AsyncClient(timeout=15.0, http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 404:
                data = response.json()
                if data.get("message") == "User not found" and data.get("statusCode") == 404:
                    return Result.available(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            if response.status_code == 201:
                data = response.json()
                if data.get("status") is True and "Password reset email has been sent" in data.get("message", ""):
                    return Result.taken(url=show_url)
                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_talkpal(email: str) -> Result:
    """
    TalkPal email validator. Note: This will send a password reset email if it exists.
    """
    return await _check(email)
