from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


_URL = "https://www.dirbam.lt/patikrinti/el-pastas"


async def validate_dirbam(email: str) -> Result:
    """Check Dirbam's email validator without creating an account."""
    show_url = "https://www.dirbam.lt"

    try:
        response = await impersonate_request_async(_URL, params={"email": email})
    except Exception as exc:
        return Result.error(exc, url=show_url)

    if response.status_code != 200:
        return Result.error(
            f"Unexpected validation response: {response.status_code}", url=show_url
        )

    try:
        result = response.json()
    except ValueError:
        return Result.error("Unexpected validation response body", url=show_url)

    if result == "Paskyra su tokių el.paštu jau yra":
        return Result.taken(url=show_url)
    if result == "true":
        return Result.available(url=show_url)
    return Result.error("Unexpected validation response body", url=show_url)
