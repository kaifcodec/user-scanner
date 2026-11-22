import json
import re
from urllib.parse import quote, unquote, urlsplit

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

_PROFILE = re.compile(
    r'<script\b[^>]*\btype=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def validate_leanpub(user: str) -> Result:
    profile_url = f"https://leanpub.com/u/{quote(user, safe='')}"

    def process(response) -> Result:
        if response.status_code == 404:
            if "errors-" in response.text or "r_error_alert" in response.text:
                return Result.available()
            return Result.error("Unexpected Leanpub not-found response")

        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        return _profile_result(response, user)

    return generic_validate(
        profile_url,
        process,
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
