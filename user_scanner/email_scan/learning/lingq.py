import httpx

from user_scanner.core.result import Result


async def validate_lingq(email: str) -> Result:
    """Check LingQ's non-loud registration field validator."""
    show_url = "https://www.lingq.com"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{show_url}/en/accounts/validate-field/",
                params={"email": email},
            )

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)
            if response.status_code != 200:
                return Result.error(
                    f"Unexpected response status: {response.status_code}",
                    url=show_url,
                )

            data = response.json()
            if data == {}:
                return Result.available(url=show_url)

            email_result = data.get("email", {})
            messages = email_result.get("message", [])
            if email_result.get("is_valid") is False and any(
                "already have an account" in message for message in messages
            ):
                return Result.taken(url=show_url)
            if email_result.get("is_valid") is False:
                return Result.error("Email rejected by LingQ", url=show_url)
            return Result.error("Unexpected response body", url=show_url)
    except (httpx.HTTPError, ValueError) as exc:
        return Result.error(exc, url=show_url)
