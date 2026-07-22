import re
import json
import html
from user_scanner.core.orchestrator import generic_validate, Result

# "Personal information" / "What I look like" row labels renamed to friendlier
# extra keys; any other row label is passed through as-is.
LABEL_RENAME = {"from": "location"}


def validate_xhamster(user):
    url = f"https://xhamster.com/users/profiles/{user}"
    show_url = url

    def process(response):
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        # A real profile echoes the exact user path in a canonical link or in the
        # embedded userModel; a 200 without either (age gate, generic landing) is
        # not a hit. Not every profile ships a canonical tag, so the userModel is
        # the reliable fallback.
        if _confirms_user(response.text, user):
            return Result.taken(extra=_extract_profile(response.text), url=show_url)

        return Result.error("Profile confirmation not found", url=show_url)

    return generic_validate(url, process, show_url=show_url)


def _confirms_user(html_text: str, user: str) -> bool:
    canonical = _canonical_profile(html_text)
    if canonical and canonical.lower() == user.lower():
        return True

    # pageURL is JSON-encoded, so slashes may arrive escaped as \/.
    return bool(re.search(
        r'"userModel"[^{}]{0,120}?"pageURL":"[^"]*?users\\?/profiles\\?/' + re.escape(user) + r'"',
        html_text, re.IGNORECASE))


def _canonical_profile(html_text: str) -> str | None:
    link = re.search(r'<link\b[^>]*\brel="canonical"[^>]*>', html_text, re.IGNORECASE)
    if not link:
        return None

    href = re.search(r'href="([^"]+)"', link.group(0), re.IGNORECASE)
    if not href:
        return None

    match = re.search(r'/users/profiles/([^/?#]+)', href.group(1), re.IGNORECASE)
    return match.group(1) if match else None


def _extract_profile(html_text: str) -> dict:
    extra = {}

    # The public "Personal information" and "What I look like" tables share the
    # same info-row markup (label div + value div, whitespace between tags).
    for row in re.finditer(
        r'<div class="info-row[^"]*">\s*<div class="label">([^<]+?):?\s*</div>\s*<div class="value">(.*?)</div>',
        html_text, re.DOTALL):
        label = re.sub(r"\s+", " ", row.group(1)).strip().lower()
        if label == "interests and fetishes":
            continue
        value = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", row.group(2))).strip()
        # Some values arrive double-encoded (e.g. "Andr&amp;eacute;" -> "André").
        value = html.unescape(html.unescape(value))
        if value:
            extra[LABEL_RENAME.get(label, label)] = value

    for label, key in (("profile views", "profile_views"), ("subscribers", "subscribers")):
        match = re.search(rf'<b>([\d.,]+[KMk]?)</b>\s*{label}', html_text, re.IGNORECASE)
        if match and match.group(1) != "0":
            extra[key] = match.group(1)

    # The owner's free-text "About me" lives in the embedded state, not an
    # info-row. profileEditableAboutMe is the page owner's field.
    about = re.search(r'"profileEditableAboutMe":\{"about":("(?:[^"\\]|\\.)*")', html_text)
    if about:
        try:
            text = json.loads(about.group(1))
        except json.JSONDecodeError:
            text = ""
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()
        if text:
            extra["about"] = text

    days = re.search(r'<b>([\d,]+) days</b>\s*on xHamster', html_text, re.IGNORECASE)
    if days:
        extra["days_on_site"] = f"{days.group(1)} days"

    last_seen = re.search(r'Last seen ([^<]+)</div>', html_text, re.IGNORECASE)
    if last_seen:
        extra["last_seen"] = last_seen.group(1).strip()

    return extra
