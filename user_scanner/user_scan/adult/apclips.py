import html
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://apclips.com"

ABOUT_STAT = re.compile(
    r'<div class="about-stat">\s*<span class="stat-label">(.*?)</span>\s*'
    r'<span class="stat-text">(.*?)</span>',
    re.DOTALL,
)


def validate_apclips(user: str) -> Result:
    url = f"{BASE_URL}/{user}"

    def process(response):
        if response.status_code in (301, 302):
            # An unknown handle is bounced to the creator directory; following the
            # redirect lands on a 200 listing page and destroys the miss signal.
            location = response.headers.get("location", "")
            if re.fullmatch(rf"(?:{re.escape(BASE_URL)})?/models/?", location):
                return Result.available()
            return Result.error(f"Unexpected redirect: {location}")

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        page = response.text
        owner = re.search(r'data-username="([^"]+)"', page)
        if not owner or owner.group(1).lower() != user.lower():
            return Result.error("Profile confirmation not found")

        return Result.taken(extra=_profile(page, user), media=_media(page, user))

    return impersonate_validate(url, process, show_url=url)


def _profile(page: str, user: str) -> dict:
    extra: dict[str, str | bool | int] = {}

    # The masthead label names the account type ("AP Model", "AP Studio").
    account_type = re.search(r'header-ctlabel"><i[^>]*></i>\s*([^<]+)<', page)
    if account_type:
        extra["type"] = _text(account_type.group(1))

    name = re.search(r'<h1 class="page-modelname[^"]*"><span>([^<]+)</span>', page)
    if name:
        extra["name"] = _text(name.group(1))

    creator_id = re.search(r'data-creator-id="(\d+)"', page)
    if creator_id:
        extra["creator_id"] = creator_id.group(1)

    bio = re.search(r'<div class="text-medium pb-2">(.*?)</div>', page, re.DOTALL)
    if bio:
        extra["bio"] = _text(bio.group(1))

    for label, value in ABOUT_STAT.findall(page):
        key = _text(label).lower().replace(" ", "_")
        if key:
            extra[key] = _text(value)

    # Section counts elsewhere on the page belong to fan-club upsells and other
    # creators, so each is read from the heading that links to this profile.
    for section in ("photosets", "bundles"):
        count = re.search(
            rf'<strong>([\d,]+)</strong>[^<]*<a href="/{re.escape(user)}/{section}"', page
        )
        if count:
            extra[section] = count.group(1)

    categories = re.findall(r'class="profile-tag-link[^"]*"[^>]*>([^<]+)</a>', page)
    if categories:
        extra["categories"] = ", ".join(_text(x) for x in categories)

    links = re.findall(
        r'<a href="([^"]+)" target="_blank" class="btn btn-outline-dark btn-block"[^>]*>'
        r'\s*<i[^>]*></i>\s*<span>([^<]*)</span>',
        page,
    )
    if links:
        extra["links"] = ", ".join(f"{_text(label)}: {href}" for href, label in links)

    return extra


def _media(page: str, user: str) -> dict:
    media = {}
    handle = re.escape(user)

    avatar = re.search(rf'src="(/ui/img/model/{handle}/avatar/[^"]+)"', page)
    if avatar:
        media["avatar"] = BASE_URL + avatar.group(1)

    banner = re.search(
        rf'id="page-mast" style="background-image: url\(/?(ui/img/model/{handle}/header/[^)]+)\)',
        page,
    )
    if banner:
        media["banner"] = f"{BASE_URL}/{banner.group(1)}"

    return media


def _text(markup: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))).strip()
