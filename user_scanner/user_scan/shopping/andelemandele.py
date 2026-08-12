import html
import json
import re
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from user_scanner.core.orchestrator import generic_validate, make_request
from user_scanner.core.result import Result

BASE_URL = "https://www.andelemandele.lv"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def validate_andelemandele(user: str) -> Result:
    username = user.strip()
    url = f"{BASE_URL}/{quote(username, safe='')}"

    def process(response):
        if response.status_code == 404 and 'page--404' in response.text and "Nav atrasts" in response.text:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        profile = re.search(
            r'<article class="user-profile\b.*?</article>',
            response.text,
            re.DOTALL,
        )
        if not profile:
            return Result.error("Could not verify profile page")

        profile_html = profile.group(0)
        profile_extra = _profile_extra(profile_html)
        profile_media = _profile_media(profile_html)

        if user_json := _product_user(response.text, profile_extra.get("id")):
            return Result.taken(extra=_json_extra(user_json), media=_json_media(user_json))

        return Result.taken(extra=profile_extra, media=profile_media)

    return generic_validate(
        url,
        process,
        headers=HEADERS,
        show_url=url,
        follow_redirects=True,
    )


def _profile_extra(profile: str) -> dict[str, str | bool | int]:
    extra: dict[str, str | bool | int] = {}

    if user_id := re.search(r'data-user_id="(\d+)"', profile):
        extra["id"] = int(user_id.group(1))

    if "verified-badge" in profile:
        extra["verified"] = True

    if name := re.search(r"<h1>\s*(.*?)\s*(?:<span|<div|</h1>)", profile, re.DOTALL):
        extra["name"] = _text(name.group(1))

    if bio := re.search(r'<p class="user-profile__about hidden-xs">(.*?)</p>', profile, re.DOTALL):
        extra["bio"] = _text(bio.group(1))

    stats = [
        _text(cell)
        for cell in re.findall(r"<td>(.*?)</td>", profile, re.DOTALL)
    ]
    if stats and (member_since := stats[0].removeprefix("Andelē jau").strip()):
        extra["member_since"] = member_since
    if len(stats) > 1 and (last_online := stats[1].removeprefix("Tiešsaistē").strip()):
        extra["last_online"] = last_online
    if len(stats) > 2 and (items := re.search(r"\d+", stats[2])):
        extra["items"] = int(items.group(0))

    return extra


def _profile_media(profile: str) -> dict[str, str]:
    avatar = re.search(r"background-image:url\('([^']+)'\)", profile)
    return {"avatar": html.unescape(avatar.group(1))} if avatar else {}


def _product_user(page: str, profile_id: object) -> dict | None:
    product = re.search(r'class="product-card__link"[^>]+href="(/perle/[^"]+/)"', page)
    if not product:
        return None

    try:
        response = make_request(f"{BASE_URL}{product.group(1)}", headers=HEADERS, follow_redirects=True)
    except (httpx.HTTPError, RuntimeError):
        return None

    if response.status_code != 200:
        return None

    user = _component_props(response.text).get("user")
    return user if isinstance(user, dict) and user.get("id") == profile_id else None


def _component_props(page: str) -> dict:
    match = re.search(
        r'data-component="UserInfoCard"[^>]+data-props="([^"]+)"',
        page,
        re.DOTALL,
    )
    if not match:
        return {}

    try:
        props = json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError:
        return {}
    return props if isinstance(props, dict) else {}


def _json_extra(user: dict) -> dict[str, object]:
    extra = {
        "id": user.get("id"),
        "display_name": user.get("display_name"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "profile_url": user.get("link"),
        "region": user.get("region"),
        "status": user.get("status"),
        "joined": _iso(user.get("joined")),
        "last_seen": _iso(user.get("last_seen")),
        "rating": user.get("rating"),
        "rating_count": user.get("rating_count"),
        "product_count": user.get("product_count"),
        "follower_count": user.get("follower_count"),
        "following": user.get("following"),
        "blocked": user.get("blocked"),
        "verification_level": user.get("verification_level"),
        "about": user.get("about"),
        "flags": user.get("flags"),
    }
    return extra


def _json_media(user: dict) -> dict[str, str]:
    for key in ("image_large", "image", "image_small", "image_xsmall"):
        avatar = user.get(key)
        if not avatar or (key == "image_large" and re.search(r"/(?:x?small|medium)/", avatar)):
            continue
        return {"avatar": avatar}
    return {}


def _iso(value: object) -> str | None:
    if not isinstance(value, int):
        return None
    return datetime.fromtimestamp(value, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _text(markup: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))).strip()
