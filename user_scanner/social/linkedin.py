from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_linkedin(user: str) -> Result:
    """
    LinkedIn username validator.

    Notes:
    - LinkedIn aggressively blocks automated traffic.
    - This validator is intentionally conservative.
    - Blocked responses are treated as 'unknown'.
    """

    url = f"https://www.linkedin.com/in/{user}/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Upgrade-Insecure-Requests': "1",
    }

    NOT_FOUND_PHRASES = (
        "This page doesn’t exist",
        "This profile is not available",
        "Page not found",
    )

    LOGIN_HINTS = (
        "Sign in to LinkedIn",
        "/login",
        "/checkpoint",
    )

    def process(response):
        status = response.status_code
        text = response.text or ""

        if status in (403, 429, 999):
            return Result.error("blocked (linkedin)")

        if status in (301, 302, 303):
            return Result.taken()

        if status == 200:
            if any(hint in text for hint in LOGIN_HINTS):
                return Result.taken()

            if any(p in text for p in NOT_FOUND_PHRASES):
                return Result.available()

            return Result.taken()

        if status == 404:
            return Result.available()
        return Result.error(f"unexpected status {status}")

    return generic_validate(
        url,
        process,
        headers=headers,
        follow_redirects=False,
    )
