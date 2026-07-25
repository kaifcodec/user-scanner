import httpx

from user_scanner.core.result import Result


async def validate_annaabi(email: str) -> Result:
    show_url = "https://annaabi.ee"

    try:
        async with httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": f"{show_url}/register.php",
            },
            timeout=15.0,
        ) as client:
            response = await client.get(
                f"{show_url}/register.php",
                params={"go": "1", "emailcheck": email},
            )

        if response.status_code != 200:
            return Result.error(
                f"Unexpected response status: {response.status_code}",
                url=show_url,
            )

        body = response.text
        taken = (
            'value="2" id="psemail"' in body
            and "Sellise emailiga kasutaja on juba registreerinud" in body
        )
        available = (
            'value="1" id="psemail"' in body and "See email on vaba" in body
        )
        if taken != available:
            return (
                Result.taken(url=show_url)
                if taken
                else Result.available(url=show_url)
            )
        return Result.error("Unexpected response body", url=show_url)
    except httpx.HTTPError as exc:
        return Result.error(exc, url=show_url)
