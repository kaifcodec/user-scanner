import re

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result

SIGNUP_URL = "https://gumroad.com/signup"
CSRF_RE = re.compile(r'<meta name="csrf-token" content="([^"]+)"')


async def validate_gumroad(email: str) -> Result:
    show_url = "https://gumroad.com"

    try:
        page = await impersonate_request_async(SIGNUP_URL, allow_redirects=True)
        if page.status_code != 200:
            return Result.error(
                f"Unexpected Gumroad signup response: {page.status_code}",
                url=show_url,
            )

        token = CSRF_RE.search(page.text)
        if not token or "Signup/New" not in page.text:
            return Result.error("Could not read Gumroad signup form", url=show_url)

        response = await impersonate_request_async(
            SIGNUP_URL,
            "POST",
            json={
                "user": {
                    "email": email,
                    # Gumroad rejects this three-character password after checking
                    # whether the email is already registered.
                    "password": "Q7~",
                },
            },
            headers={
                "accept": "text/html, application/xhtml+xml",
                "origin": "https://gumroad.com",
                "referer": SIGNUP_URL,
                "x-csrf-token": token.group(1),
                "x-inertia": "true",
                "x-requested-with": "XMLHttpRequest",
            },
            allow_redirects=True,
        )
        if response.status_code != 200:
            return Result.error(
                f"Unexpected Gumroad signup response: {response.status_code}",
                url=show_url,
            )

        data = response.json()
        if data.get("component") != "Signup/New":
            return Result.error("Unexpected Gumroad signup page", url=show_url)

        flash = data.get("props", {}).get("flash") or {}
        message = flash.get("message")
        if message == "An account already exists with this email.":
            return Result.taken(url=show_url)
        if message == "Password is too short (minimum is 4 characters)":
            return Result.available(url=show_url)
        return Result.error("Unexpected Gumroad signup result", url=show_url)
    except Exception as exc:
        return Result.error(exc, url=show_url)
