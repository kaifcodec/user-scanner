import re
from user_scanner.core.orchestrator import generic_validate, Result


def validate_xhamster(user):
    url = f"https://xhamster.com/users/profiles/{user}"
    show_url = url

    def process(response):
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        # A real profile answers 200 with a canonical link echoing the exact
        # user path; a 200 without it (age gate, generic landing) is not a hit.
        canonical = _canonical_profile(response.text)
        if canonical and canonical.lower() == user.lower():
            return Result.taken(url=show_url)

        return Result.error("Profile confirmation not found", url=show_url)

    return generic_validate(url, process, show_url=show_url)


def _canonical_profile(html: str) -> str | None:
    link = re.search(r'<link\b[^>]*\brel="canonical"[^>]*>', html, re.IGNORECASE)
    if not link:
        return None

    href = re.search(r'href="([^"]+)"', link.group(0), re.IGNORECASE)
    if not href:
        return None

    match = re.search(r'/users/profiles/([^/?#]+)', href.group(1), re.IGNORECASE)
    return match.group(1) if match else None
