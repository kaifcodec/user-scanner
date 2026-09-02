import html
import json
import re
from urllib.parse import quote, unquote, urlsplit

from user_scanner.core.orchestrator import generic_validate
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
_USERNAME_TAKEN = "Username has already been taken"
_PROFILE = re.compile(
    r'<script\b[^>]*\btype=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def validate_leanpub(user: str) -> Result:
    profile_url = f"https://leanpub.com/u/{quote(user, safe='')}"

    def process(response):
        if response.status_code != 200 or _PASSWORD_ERROR not in response.text:
            return Result.error(
                f"Unexpected Leanpub registration response: {response.status_code}"
            )

        username_input = re.search(
            r'<input\b(?=[^>]*\bname="username")[^>]*>',
            response.text,
            re.IGNORECASE,
        )
        value = (
            re.search(r'\bvalue="([^"]*)"', username_input.group(), re.IGNORECASE)
            if username_input
            else None
        )
        if not value or html.unescape(value.group(1)) != user:
            return Result.error("Leanpub did not echo the requested username")

        if _USERNAME_TAKEN in response.text:
            enrichment = generic_validate(
                profile_url,
                lambda profile_response: _profile_result(profile_response, user),
                follow_redirects=True,
            )
            return enrichment if enrichment.extra else Result.taken()

        if 'aria-invalid="true"' not in username_input.group():
            return Result.available()

        return Result.error("Leanpub returned an unknown username validation error")

    return generic_validate(
        _REGISTRATION_URL,
        process,
        method="POST",
        data={
            "title": "Username availability probe",
            "publisherId": _PUBLISHER_ID,
            "slug": "user-scanner-username-probe",
            "languageId": _ENGLISH_ID,
            "syncMode": "lexical",
            "name": "Username Probe",
            "username": user,
            "email": "user-scanner@example.com",
            "password": "x",  # Intentionally invalid; the probe cannot create an account.
        },
        show_url=profile_url,
        follow_redirects=True,
    )


def _profile_result(response, user: str) -> Result:
    if response.status_code != 200:
        return Result.error(f"Unexpected profile response: {response.status_code}")

    profile = None
    books = None
    for block in _PROFILE.findall(response.text):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("@type") == "Person":
            profile = data
        elif data.get("@type") == "ItemList" and str(data.get("@id", "")).endswith(
            "#books"
        ):
            books = data

    if profile is None:
        return Result.error("Leanpub profile markers were missing")

    parsed_url = urlsplit(str(profile.get("url", "")))
    username = unquote(parsed_url.path.rstrip("/").rsplit("/", 1)[-1])
    if parsed_url.hostname != "leanpub.com" or username.casefold() != user.casefold():
        return Result.error("Leanpub profile did not match the requested username")

    book_count = books.get("numberOfItems") if books else None
    if type(book_count) is not int or book_count < 0:
        book_count = None

    return Result.taken(
        extra={
            "username": username,
            "name": profile.get("name"),
            "bio": profile.get("description"),
            "social_links": profile.get("sameAs") or None,
            "book_count": book_count,
        },
        media={"avatar": profile.get("image")},
    )
