import httpx

from user_scanner.core.result import Result


async def validate_speakly(email: str) -> Result:
    """Check Speakly's reset endpoint. Sends email for registered accounts."""
    show_url = "https://speakly.me"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.v4.speakly.me/api/v4/users/password/reset/",
                json={"email": email},
            )

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)
            if response.status_code == 400:
                data = response.json()
                if data == ["Email not found."]:
                    return Result.available(url=show_url)
                return Result.error("Email rejected by Speakly", url=show_url)
            # Speakly's frontend treats any resolved reset request as success.
            if response.status_code == 200:
                return Result.taken(url=show_url)
            return Result.error(
                f"Unexpected response status: {response.status_code}",
                url=show_url,
            )
    except (httpx.HTTPError, ValueError) as exc:
        return Result.error(exc, url=show_url)
