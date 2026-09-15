import html
import re

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result

SIGNUP_URL = "https://profile.threadless.com/artist/shops/"
CSRF_RE = re.compile(r"name=['\"]csrfmiddlewaretoken['\"]\s+value=['\"]([^'\"]+)")


def validate_threadless_shop(user: str) -> Result:
    shop = user.lower()
    show_url = f"https://{shop}.threadless.com/"
    if not re.fullmatch(r"[a-z0-9]{1,63}", shop):
        return Result.error(
            "Shop name must contain only lowercase letters and numbers",
            url=show_url,
        )

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
                "shop_name": shop,
                "csrfmiddlewaretoken": token.group(1),
            },
        )
        if response.status_code != 200:
            return Result.error(
                f"Unexpected Threadless response: HTTP {response.status_code}"
            )

        match response.json():
            case {"is_valid": True}:
                return Result.available()
            case {"is_valid": False}:
                profile = _shop_profile(shop)
                if profile:
                    extra, media = profile
                    return Result.taken(extra=extra, media=media)
                return Result.error(
                    "Shop name is unavailable but no public shop was found"
                )
            case _:
                return Result.error("Unexpected Threadless response")

    return impersonate_validate(
        SIGNUP_URL,
        process,
        show_url=show_url,
        allow_redirects=True,
    )


def _shop_profile(shop: str) -> tuple[dict, dict] | None:
    try:
        response = impersonate_request(
            f"https://{shop}.threadless.com/", allow_redirects=True
        )
    except RequestException:
        return None

    if response.status_code != 200:
        return None

    document = response.text
    brand = _text(r'data-artist-brand="([^"]+)"', document)
    if not brand or brand.casefold() != shop.casefold():
        return None

    about = ""
    try:
        about_response = impersonate_request(
            f"https://{shop}.threadless.com/about", allow_redirects=True
        )
        if about_response.status_code == 200:
            about_brand = _text(r'data-artist-brand="([^"]+)"', about_response.text)
            if about_brand and about_brand.casefold() == shop.casefold():
                about = about_response.text
    except RequestException:
        pass

    social_links = []
    website = None
    for url, kind in re.findall(
        r'<a class="aboutSocial-cta" href="([^"]+)".*?'
        r'<em class="aboutSocial-title">\s*([^<]+)',
        about,
        re.DOTALL,
    ):
        url, kind = html.unescape(url), kind.strip().lower()
        if kind == "website":
            website = url
        else:
            social_links.append(f"{kind}: {url}")

    title = _text(r'<meta property="og:title"\s+content="([^"]+)"', document)
    name = title.split(" | ", 1)[0].removesuffix("'s Artist Shop") if title else None
    return (
        {
            "name": name,
            "description": _text(
                r'<meta property="og:description"\s+content="([^"]+)"',
                document,
            ),
            "owner_id": _number(r'data-to-follow="(\d+)"', document)
            or _number(r'data-shop-user-id="(\d+)"', document),
            "owner_name": _text(
                r'<strong class="aboutProfile-title">(.*?)</strong>', about
            ),
            "location": _text(r'<p class="aboutProfile-subtitle">(.*?)</p>', about),
            "headline": _clean(
                r'<h2 class="(?=[^"]*\baboutTitle\b)'
                r'(?![^"]*\b_is-hidden\b)[^"]*">(.*?)</h2>',
                about,
            ),
            "biography": _clean(r'<div class="aboutContent-bio">(.*?)</div>', about),
            "website": website,
            "social_links": ", ".join(social_links),
            "search_enabled": _has_link("search", document),
            "gift_cards_enabled": _has_link("gift-cards", document),
            "wholesale_enabled": _has_link("wholesale", document),
            "self_reported_shop_profiles": ", ".join(
                _clean_text(badge)
                for badge in re.findall(r'<div class="badge-title">\s*([^<]+)', about)
            ),
        },
        {
            "logo": _text(r'<img src="([^"]+)" alt="A logo image for', document),
            "cover": _text(
                r'<link rel="preload" media="\(min-width: 651px\)" href="([^"]+)"',
                document,
            ),
            "preview": _text(
                r'<meta property="og:image"\s+content="([^"]+)"', document
            ),
            "bio_photo": _text(
                r'<img class="aboutProfile aboutProfile--img" src="([^"]+)"',
                about,
            ),
        },
    )


def _text(pattern: str, document: str) -> str | None:
    match = re.search(pattern, document, re.DOTALL)
    return html.unescape(match.group(1)).strip() if match else None


def _number(pattern: str, document: str) -> int | None:
    value = _text(pattern, document)
    return int(value) if value else None


def _has_link(path: str, document: str) -> bool:
    return bool(
        re.search(
            rf'<a\b[^>]*\bhref="(?:https?://[^/"]+)?/{re.escape(path)}/?'
            r'(?:\?[^"]*)?"',
            document,
        )
    )


def _clean(pattern: str, document: str) -> str | None:
    value = _text(pattern, document)
    return _clean_text(value) if value else None


def _clean_text(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())
