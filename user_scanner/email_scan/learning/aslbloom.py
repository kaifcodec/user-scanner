import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://app.aslbloom.com/api/searchForUser"
    show_url = "https://www.aslbloom.com"

    headers = {
        "User-Agent": "okhttp/4.12.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }

    payload = {
        "email": email,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                found_user = data.get("foundUser")

                if found_user == "YES":
                    return Result.taken(url=show_url)

                if found_user == "NO":
                    return Result.available(url=show_url)

                return Result.error(
                    "Unexpected response body, report it via GitHub issues",
                    url=show_url,
                )

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_aslbloom(email: str) -> Result:
    """
    ASL Bloom email validator.
    Checks searchForUser API endpoint.
    """
    return await _check(email)
