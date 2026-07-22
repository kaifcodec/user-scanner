import re
import html
from user_scanner.core.orchestrator import generic_validate, Result


def validate_faproulette(user):
    url = f"https://faproulette.co/@{user}"
    show_url = url

    def process(response):
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        # A real profile answers 200 with a canonical link echoing /@{user}; a
        # 200 without it (age gate, generic landing) is not a hit.
        canonical = _canonical_user(response.text)
        if canonical and canonical.lower() == user.lower():
            return Result.taken(extra=_extract_profile(response.text), url=show_url)

        return Result.error("Profile confirmation not found", url=show_url)

    return generic_validate(url, process, show_url=show_url)


def _canonical_user(html_text: str) -> str | None:
    link = re.search(r'<link\b[^>]*\brel="canonical"[^>]*>', html_text, re.IGNORECASE)
    if not link:
        return None

    href = re.search(r'href="([^"]+)"', link.group(0), re.IGNORECASE)
    if not href:
        return None

    match = re.search(r'/@([^/?#]+)', href.group(1))
    return match.group(1) if match else None


def _extract_profile(html_text: str) -> dict:
    extra = {}

    # og:title is "<DisplayName>'s Profile - Fap Roulette"; the apostrophe may
    # arrive raw or html-encoded depending on the rendering path.
    name = re.search(
        r'og:title"\s+content="(.+?)(?:&#0?39;|&apos;|\')s Profile',
        html_text, re.IGNORECASE)
    if name:
        extra["name"] = html.unescape(name.group(1)).strip()

    joined = re.search(
        r'<span class="type">Joined</span>.{0,200}?(\d{4}-\d{2}-\d{2})',
        html_text, re.IGNORECASE | re.DOTALL)
    if joined:
        extra["joined"] = joined.group(1)

    roulettes = re.search(r'roulettes_total(?:&quot;|")\s*:\s*(\d+)', html_text, re.IGNORECASE)
    if roulettes:
        extra["roulettes"] = roulettes.group(1)

    return extra
