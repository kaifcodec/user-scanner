from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def validate_annaabi(email: str) -> Result:
    show_url = "https://annaabi.ee"

    try:
        response = await impersonate_request_async(
            f"{show_url}/register.php",
            params={"go": "1", "emailcheck": email},
            headers={"Referer": f"{show_url}/register.php"},
            allow_redirects=True,
        )

        # Cloudflare serves a managed challenge to some clients; no HTTP client
        # can clear it, so never turn it into a verdict.
        if response.headers.get("cf-mitigated") == "challenge":
            return Result.error(
                "Cloudflare challenge, cannot be solved without a browser",
                url=show_url,
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
    except Exception as exc:
        return Result.error(exc, url=show_url)
