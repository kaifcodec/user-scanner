import re

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


_URL = "https://www.kandideeri.ee/registration/?user_group_id=JobSeeker"


async def validate_kandideeri(email: str) -> Result:
    """Check Kandideeri's signup validator without creating an account."""
    show_url = "https://www.kandideeri.ee"

    try:
        page = await impersonate_request_async(_URL)
        if page.status_code != 200 or 'id="registr-form"' not in page.text:
            return Result.error(
                f"Unexpected signup page response: {page.status_code}",
                url=show_url,
            )

        token = re.search(
            r'<meta name="csrf-token" content="([^"]+)"', page.text
        )
        if not token:
            return Result.error("Could not find Kandideeri CSRF token", url=show_url)

        response = await impersonate_request_async(
            _URL,
            method="POST",
            data={
                "csrf-token": token.group(1),
                "username": email,
                "validate_username": "✓",
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
    except Exception as exc:
        return Result.error(exc, url=show_url)

    if response.status_code != 200:
        return Result.error(
            f"Unexpected validation response: {response.status_code}", url=show_url
        )
    if response.text == "NOT_UNIQUE_VALUE":
        return Result.taken(url=show_url)
    if response.text == "":
        return Result.available(url=show_url)
    return Result.error("Unexpected validation response body", url=show_url)
