import httpx

from user_scanner.core.result import Result


async def validate_speak(email: str) -> Result:
    """Check Speak's non-loud registration email lookup."""
    show_url = "https://app.speak.com"
    url = (
        "https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri"
        "?key=AIzaSyAbB_C9TGxqWryYcmx74MeTTeUXdUB4HU4"
    )
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                json={
                    "identifier": email,
                    "continueUri": f"{show_url}/us-en/register/email",
                },
                headers={"Origin": show_url},
            )

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)
            if response.status_code != 200:
                return Result.error(
                    f"Unexpected response status: {response.status_code}",
                    url=show_url,
                )

            data = response.json()
            if data.get("registered") is True:
                return Result.taken(url=show_url)
            if data.get("registered") is False:
                return Result.available(url=show_url)
            return Result.error("Unexpected response body", url=show_url)
    except (httpx.HTTPError, ValueError) as exc:
        return Result.error(exc, url=show_url)
