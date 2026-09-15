import httpx

from user_scanner.core.result import Result

URL = "https://be-lb-app.scaleabout.com/api/v1/auth/email/is_registered"


async def validate_wisio(email: str) -> Result:
    show_url = "https://www.wisio.com"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(URL, params={"email": email})
    except httpx.HTTPError as exc:
        return Result.error(exc, url=show_url)

    if response.status_code != 200:
        return Result.error(
            f"Unexpected Wisio response: {response.status_code}", url=show_url
        )
    if response.text.strip() == "true":
        return Result.taken(url=show_url)
    if response.text.strip() == "false":
        return Result.available(url=show_url)
    return Result.error("Unexpected Wisio response body", url=show_url)
