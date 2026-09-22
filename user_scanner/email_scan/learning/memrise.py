import re

import httpx

from user_scanner.core.result import Result


async def validate_memrise(email: str) -> Result:
    """Check Memrise's password reset form. Sends email for registered accounts."""
    url = "https://app.memrise.com/password/reset/"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            initial = await client.get(url)
            if initial.status_code != 200:
                return Result.error(
                    f"Unexpected initial response status: {initial.status_code}",
                    url=url,
                )

            match = re.search(
                r'name="csrfmiddlewaretoken" value="([^"]+)"', initial.text
            )
            if not match:
                return Result.error("Unable to extract CSRF token", url=url)

            response = await client.post(
                url,
                data={"csrfmiddlewaretoken": match.group(1), "email": email},
                headers={"Referer": url},
            )

            if (
                response.status_code == 302
                and response.headers.get("location") == "/password/reset/done/"
            ):
                return Result.taken(url="https://www.memrise.com")
            if response.status_code == 200 and "No such user." in response.text:
                return Result.available(url="https://www.memrise.com")
            if response.status_code == 429:
                return Result.error("Rate limited", url=url)
            return Result.error(
                f"Unexpected response status: {response.status_code}", url=url
            )
    except httpx.HTTPError as exc:
        return Result.error(exc, url=url)
