import httpx

from user_scanner.core.result import Result


async def validate_mondly(email: str) -> Result:
    """Check Mondly's login endpoint without sending email."""
    url = "https://api.mondly.com/v1/user/login"
    show_url = "https://app.mondly.com"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                data={"email": email, "password": "scanner-invalid-password"},
            )

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)
            if response.status_code != 200:
                return Result.error(
                    f"Unexpected response status: {response.status_code}",
                    url=show_url,
                )

            data = response.json()
            if data.get("errors", {}).get("password") == ["incorrect"]:
                return Result.taken(url=show_url)
            if data.get("errors", {}).get("password") == ["not-found"]:
                return Result.available(url=show_url)
            return Result.error("Unexpected response body", url=show_url)
    except (httpx.HTTPError, ValueError) as exc:
        return Result.error(exc, url=show_url)
