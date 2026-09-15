import html
import re
from urllib.parse import quote, urljoin

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result

SIGNUP_URL = "https://profile.threadless.com/artist/shops/"
CSRF_RE = re.compile(r"name=['\"]csrfmiddlewaretoken['\"]\s+value=['\"]([^'\"]+)")


def validate_threadless(user: str) -> Result:
    show_url = f"https://www.threadless.com/@{user}"

    def process(page):
        token = CSRF_RE.search(page.text)
        if page.status_code != 200 or not token:
            return Result.error(
                f"Could not read Threadless signup form (HTTP {page.status_code})"
            )

        response = impersonate_request(
            SIGNUP_URL,
            "POST",
            headers={"x-requested-with": "XMLHttpRequest"},
            data={
                "validate": "true",
                "username": user,
                "csrfmiddlewaretoken": token.group(1),
            },
        )
        if response.status_code != 200:
            return Result.error(
                f"Unexpected Threadless response: HTTP {response.status_code}"
            )

        match response.json():
            case {"is_valid": False}:
                extra, media = _profile(user)
                return Result.taken(extra=extra, media=media)
            case {"is_valid": True}:
                return Result.available()
            case _:
                return Result.error("Unexpected Threadless response")

    return impersonate_validate(
        SIGNUP_URL,
        process,
        show_url=show_url,
        allow_redirects=True,
    )


def _profile(user: str) -> tuple[dict, dict]:
    try:
        response = impersonate_request(
            f"https://www.threadless.com/@{quote(user, safe='')}",
            allow_redirects=True,
        )
    except RequestException:
        return {}, {}

    if response.status_code != 200:
        return {}, {}

    document = response.text
    username = _text(r'var userName = "([^"]+)"', document)
    if not username or username.casefold() != user.casefold():
        return {}, {}

    shop = _text(r'<div class="artist-shop">(.*?)</div>', document) or ""
    shop_url = _text(r'<a href="([^"]+)" title="Visit my Artist Shop"', shop)
    links = re.findall(
        r'<a href="(https?://[^"]+)" target="_blank" title="[^"]+" rel="nofollow"',
        document,
    )
    website = _text(
        r'<div class="website">(?:(?!</div>).)*?<a href="([^"]+)"', document
    )
    shop_preview = _text(r'<img src="([^"]+)"', shop)
    return (
        {
            "id": _text(r"var profileId = (\d+);", document),
            "name": _text(r'<span class="name">\s*([^<]+)', document),
            "bio": _text(r'<div class="cover-statement">\s*<p>(.*?)</p>', document),
            "location": _text(
                r'<div class="location">\s*<h3>Location</h3>\s*([^<]+)', document
            ),
            "following": _text(r'/following"[^>]*>\s*<span>(\d+)</span>', document),
            "followers": _text(r'/followers"[^>]*>\s*<span>(\d+)</span>', document),
            "member_since": _text(r"Member since ([^<]+)", document),
            "artist_shop": urljoin("https://www.threadless.com", shop_url)
            if shop_url
            else None,
            "artist_shop_slug": _text(r'var artistSlug = "([^"]+)";', document),
            "artist_shop_name": _text(
                r'title="Visit my Artist Shop"[^>]*>\s*([^<]+)</a>',
                shop,
            ),
            "website": website,
            "links": ", ".join(map(html.unescape, links)),
            "threads_started": _number(r"([\d,]+) threads started", document),
            "designs_submitted": _number(r"([\d,]+) designs submitted", document),
            "designs_scored": _number(r"([\d,]+) designs scored", document),
            "avg_score_given": _text(r"Avg Score Given:\s*([\d.]+)", document),
            "is_printed_artist": _flag("isPrintedArtist", document),
            "is_submitted_artist": _flag("isSubmittedArtist", document),
            "is_shop_owner": _flag("isShopOwner", document),
            "facebook_connected": _flag("fbConnected", document),
            "is_hifiver": _flag("isHifiver", document),
            "is_shop_published": _flag("isShopPublished", document),
            "open_submissions": _flag("openSubs", document),
            "is_alumni": "is-alumni" in document,
        },
        {
            "avatar": _text(r'<meta property="og:image" content="([^"]+)"', document),
            "cover": _text(
                r'<header id="header" style="background-image: url\([\'\"]([^\'\"]+)',
                document,
            ),
            "artist_shop_preview": shop_preview,
        },
    )


def _text(pattern: str, document: str) -> str | None:
    match = re.search(pattern, document, re.DOTALL)
    return html.unescape(match.group(1)).strip() if match else None


def _number(pattern: str, document: str) -> int | None:
    value = _text(pattern, document)
    return int(value.replace(",", "")) if value else None


def _flag(name: str, document: str) -> bool | None:
    value = _text(rf"var {name} = (true|false);", document)
    return value == "true" if value else None
