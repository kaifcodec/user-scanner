import re

import httpx

from user_scanner.core.helpers import get_global_timeout, get_proxy
from user_scanner.core.result import Result


async def validate_meetnfly(email: str) -> Result:
    """Loud: submit MeetnFly's password-reset form with an isolated cookie session."""
    show_url = "https://meetnfly.com/forgot-password"
    try:
        async with httpx.AsyncClient(
            proxy=get_proxy(),
            timeout=get_global_timeout() or 15.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        ) as client:
            page = await client.get(show_url)
            token = re.search(r'name="_token" value="([^"]+)"', page.text)
            if page.status_code != 200 or not token:
                return Result.error("Could not obtain password-reset token", url=show_url)
            response = await client.post(
                show_url,
                data={"_token": token.group(1), "email": email},
                headers={"Referer": show_url},
            )

        if response.status_code == 422:
            data = response.json()
            if (
                isinstance(data, dict)
                and isinstance(data.get("errors"), dict)
                and data["errors"].get("email") == [
                    "Ei suutnud leida sellise e-posti aadressiga kasutajat."
                ]
            ):
                return Result.available(url=show_url)
        if (
            response.status_code == 200
            and str(response.url) == show_url
            and response.history
            and response.history[0].status_code == 302
            and re.search(
                r'<div\b[^>]*class="[^"]*\btext-green-600\b[^"]*"[^>]*>\s*\S',
                response.text,
            )
        ):
            # Laravel renders its reset-success session status in this green box.
            return Result.taken(url=show_url)
        return Result.error(
            f"Unexpected password-reset response: {response.status_code}", url=show_url
        )
    except (httpx.HTTPError, ValueError) as exc:
        return Result.error(exc, url=show_url)
