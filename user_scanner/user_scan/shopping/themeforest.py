import html
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://themeforest.net"

# Cloudflare answers every other curl_cffi fingerprint (including the default
# "chrome") with a "Just a moment..." interstitial on this host; "safari184" is
# the only profile that reaches the origin.
IMPERSONATE = "safari184"

BIO_MAX_LENGTH = 500


def validate_themeforest(user: str) -> Result:
    url = f"{BASE_URL}/user/{user}"

    def process(response):
        page = response.text

        if _is_challenge(page):
            return Result.error("Blocked by a Cloudflare challenge")

        if response.status_code == 404:
            if _title(page) == "Page Not Found | ThemeForest":
                return Result.available()
            return Result.error("Unexpected 404 (not the not-found page)")

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        # A live profile is titled "<handle>'s profile on ThemeForest" and
        # canonicalises to the handle's own URL; both miss pages fall back to
        # the generic site chrome.
        canonical = re.search(r'<link rel="canonical" href="[^"]*/user/([^"/]+)"', page)
        if not canonical or canonical.group(1).lower() != user.lower():
            return Result.error("Profile confirmation not found")

        extra, media = _extract_profile(page)
        return Result.taken(extra=extra, media=media)

    return impersonate_validate(
        url,
        process,
        impersonate=IMPERSONATE,
        show_url=url,
        allow_redirects=True,
    )


def _extract_profile(page: str) -> tuple[dict, dict]:
    extra: dict = {}
    media: dict = {}

    header = _slice(page, '<div class="user-info-header', "user-info-header__tabs")

    name = re.search(r"<h1[^>]*>(.*?)</h1>", header, re.DOTALL)
    if name:
        extra["display_name"] = _text(name.group(1))

    level = re.search(
        r'user-info-header__author-level"[^>]*>\s*<strong>(.*?)</strong>', header, re.DOTALL
    )
    if level:
        extra["author_level"] = _text(level.group(1))

    # The subtitle line reads "<Country>, Member since <Month Year>", and drops
    # the country for accounts that expose no location.
    subtitle = re.search(r'<p class="t-body -size-m h-p0 h-mb0">(.*?)</p>', header, re.DOTALL)
    if subtitle:
        parts = re.match(r"(?:(.*?),\s*)?Member since (.+)$", _text(subtitle.group(1)))
        if parts:
            extra["location"] = parts.group(1)
            extra["member_since"] = parts.group(2)

    rating = re.search(r'<span class="is-visually-hidden">([\d.]+) stars</span>', header)
    if rating:
        extra["author_rating"] = rating.group(1)

    ratings = re.search(r"\(([\d,]+) ratings\)", header)
    if ratings:
        extra["ratings"] = ratings.group(1)

    # Only authors carry a sales figure, so its presence is what separates a
    # selling account from a plain marketplace member.
    sales = re.search(r'itemprop="interactionCount" content="AuthorSales:([\d,]+)"', header)
    if sales:
        extra["sales"] = sales.group(1)
    extra["account_type"] = "author" if sales else "member"

    for tab in ("followers", "following"):
        count = re.search(
            rf'href="/user/[^"]+/{tab}">[^<]*<span[^>]*>([\d,]+)</span>', page, re.IGNORECASE
        )
        if count:
            extra[tab] = count.group(1)

    bio = _text(_slice(page, '<div class="user-html"', "</div>"))
    if bio:
        extra["bio"] = bio if len(bio) <= BIO_MAX_LENGTH else f"{bio[:BIO_MAX_LENGTH]}..."

    badges = re.findall(r'data-title="([^"]+)"', _slice(page, "user-info__badges", "</ul>"))
    if badges:
        extra["badges"] = "; ".join(html.unescape(badge) for badge in badges)

    avatar = re.search(
        r'data-src="([^"]+)"[^>]*user-info-header__user-profile-image-placeholder', header
    ) or re.search(r'<img[^>]+src="([^"]+)"', header)
    # Accounts without an uploaded avatar are served a shared placeholder image.
    if avatar and "default-user" not in avatar.group(1):
        media["avatar"] = avatar.group(1)

    return extra, media


def _is_challenge(page: str) -> bool:
    return _title(page) == "Just a moment..."


def _title(page: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", page, re.IGNORECASE | re.DOTALL)
    return _text(match.group(1)) if match else ""


def _slice(page: str, start_marker: str, end_marker: str) -> str:
    start = page.find(start_marker)
    if start < 0:
        return ""
    end = page.find(end_marker, start + len(start_marker))
    return page[start:end] if end > 0 else page[start:]


def _text(markup: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", markup))).strip()
