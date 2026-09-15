import re

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result

SIGNUP_URL = "https://codepen.io/accounts/signup/user/free"


async def validate_codepen(email: str) -> Result:
    show_url = "https://codepen.io"

    try:
        page = await impersonate_request_async(SIGNUP_URL)
        token = re.search(r'<meta name="csrf-token" content="([^"]+)"', page.text)
        if page.status_code != 200 or not token:
            return Result.error(
                f"Could not read CodePen signup form ({page.status_code})",
                url=show_url,
            )

        response = await impersonate_request_async(
            "https://codepen.io/accounts/duplicate_check",
            "POST",
            headers={"x-csrf-token": token.group(1)},
            data={"attribute": "email", "value": email, "context": "user"},
        )
        if response.status_code != 200:
            return Result.error(
                f"Unexpected CodePen response: {response.status_code}", url=show_url
            )

        data = response.json()
        if data.get("success") is not True:
            return Result.error("Unexpected CodePen response", url=show_url)

        errors = data.get("payload", {}).get("errors", {}).get("email")
        if errors == ["That Email is already taken. Please choose another!"]:
            return Result.taken(url=show_url)
        if errors == []:
            return Result.available(url=show_url)
        return Result.error("Unexpected CodePen email result", url=show_url)
    except Exception as exc:  # noqa: BLE001 - scanner modules must return errors
        return Result.error(exc, url=show_url)
