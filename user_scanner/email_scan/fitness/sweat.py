import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://login.sweat.com/oauth/token"
    show_url = "https://sweat.com"

    payload = {
        "client_id": "ekN6uujzIgNGOxe8gu6XkmhSyhlnmt31",
        "scope": "openid email offline_access profile",
        "username": email,
        "password": "dummy_password_xyz123",
        "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
        "realm": "Username-Password-Authentication",
    }

    headers = {
        "User-Agent": "okhttp/5.3.2",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json; charset=utf-8",
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 403:
                data = response.json()
                error_desc = str(data.get("error_description", "")).lower()

                if "password is incorrect" in error_desc:
                    return Result.taken(url=show_url)

                if "couldn’t find an account" in error_desc or "couldn't find an account" in error_desc:
                    return Result.available(
                        reason="Target may have an OAuth-only registered account (Apple, Google, or Facebook)",
                        url=show_url,
                    )

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_sweat(email: str) -> Result:
    """
    Sweat fitness app email validator.
    Checks Auth0 password-realm oauth token endpoint with a dummy password.
    """
    return await _check(email)
