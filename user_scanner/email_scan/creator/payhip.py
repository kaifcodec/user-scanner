import httpx

from user_scanner.core.result import Result


async def validate_payhip(email: str) -> Result:
    url = "https://payhip.com/auth/forgot_password_buyer_ajax"
    show_url = "https://payhip.com"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                data={"login": email},
                headers={
                    "origin": show_url,
                    "referer": f"{show_url}/auth/forgot_password",
                    "x-requested-with": "XMLHttpRequest",
                },
            )

        if response.status_code != 200:
            return Result.error(f"HTTP {response.status_code}", url=show_url)

        try:
            data = response.json()
        except ValueError:
            return Result.error("Unexpected non-JSON response", url=show_url)

        if data.get("success") is True:
            return Result.taken(url=show_url)
        if (
            data.get("success") is False
            and data.get("error_message_public") == "Login or email doesn't exist"
        ):
            return Result.available(url=show_url)
        return Result.error("Unexpected password-reset response", url=show_url)
    except Exception as exc:
        return Result.error(exc, url=show_url)
