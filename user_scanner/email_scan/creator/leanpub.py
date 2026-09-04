import html
import re

import httpx

from user_scanner.core.result import Result

_REGISTRATION_URL = "https://leanpub.com/authors/create/book"
# Leanpub's default publisher; this decodes to gid://leanpub/Org::Publisher/1.
_PUBLISHER_ID = "Z2lkOi8vbGVhbnB1Yi9Pcmc6OlB1Ymxpc2hlci8x"
_ENGLISH_ID = "Z2lkOi8vbGVhbnB1Yi9TaGFyZWQ6Okxhbmd1YWdlLzEyNA"
_PASSWORD_ERROR = (
    "Password must be at least 8 characters long, be no longer than 140 "
    "characters, contain at least one letter, and contain at least one "
    "non-letter character."
)
_EMAIL_TAKEN = (
    "Email This email address can not be used to create a new account. "
    "If this is your email address, try signing in instead."
)


async def validate_leanpub(email: str) -> Result:
    """Probe registration without creating an account or sending email."""
    show_url = "https://leanpub.com"
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.post(
                _REGISTRATION_URL,
                data={
                    "title": "Email availability probe",
                    "publisherId": _PUBLISHER_ID,
                    "slug": "user-scanner-email-probe",
                    "languageId": _ENGLISH_ID,
                    "syncMode": "lexical",
                    "name": "Email Probe",
                    "username": "user-scanner-email-probe",
                    "email": email,
                    "password": "x",  # Intentionally too short; creation is impossible.
                },
            )
    except httpx.HTTPError as exc:
        return Result.error(exc, url=show_url)

    if response.status_code != 200 or _PASSWORD_ERROR not in response.text:
        return Result.error(
            f"Unexpected Leanpub registration response: {response.status_code}",
            url=show_url,
        )

    email_input = re.search(
        r'<input\b(?=[^>]*\bname="email")[^>]*>', response.text, re.IGNORECASE
    )
    email_tag = email_input.group() if email_input else ""
    value = re.search(r'\bvalue="([^"]*)"', email_tag, re.IGNORECASE)
    if not value or html.unescape(value.group(1)).casefold() != email.casefold():
        return Result.error("Leanpub did not echo the requested email", url=show_url)

    if _EMAIL_TAKEN in response.text:
        return Result.taken(url=show_url)

    if 'aria-invalid="true"' not in email_tag:
        return Result.available(url=show_url)

    return Result.error(
        "Leanpub returned an unknown email validation error", url=show_url
    )
