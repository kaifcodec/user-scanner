import re

import httpx

from user_scanner.core.result import Result


async def validate_weawow(email: str) -> Result:
    show_url = "https://weawow.com"
    path = "/en/password/email"

    try:
        async with httpx.AsyncClient(
            base_url=show_url, follow_redirects=True, timeout=15.0
        ) as client:
            page = await client.get(path)
            if page.status_code != 200:
                return Result.error(
                    f"Failed to access reset page: {page.status_code}", url=show_url
                )

            token = re.search(r'name="_token" value="([^"]+)"', page.text)
            if not token:
                return Result.error("Could not find CSRF token", url=show_url)

            response = await client.post(
                path,
                data={
                    "_token": token.group(1),
                    "email": email,
                },
            )

            if (
                response.status_code == 429
                or "There are too many requests." in response.text
            ):
                return Result.error("Rate limited", url=show_url)
            if response.status_code != 200:
                return Result.error(
                    f"Unexpected response status: {response.status_code}",
                    url=show_url,
                )
            if "We have e-mailed your password reset link!" in response.text:
                return Result.taken(url=show_url)
            if "find a user with that e-mail address." in response.text:
                return Result.available(url=show_url)
            return Result.error("Unexpected response body", url=show_url)
    except httpx.HTTPError as exc:
        return Result.error(exc, url=show_url)
