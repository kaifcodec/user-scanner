import html
import re

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://www.adultism.com"


def validate_adultism(user: str) -> Result:
    url = f"{BASE_URL}/profile/{user}"

    def process(response):
        if response.status_code == 404:
            if "No such member" in response.text:
                return Result.available(url=url)
            return Result.error("Unexpected 404 (not the not-found page)", url=url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=url)

        profile = _profile_section(response.text)
        if profile is None:
            return Result.error("Profile confirmation not found", url=url)

        # Lookups are case-insensitive and the heading carries the canonical
        # spelling, so it is what ties the page to the requested handle.
        nick = _nick(profile)
        if nick.lower() != user.lower():
            return Result.error("Profile heading does not match the handle", url=url)

        extra, media = _extract_profile(profile, nick)
        extra.update(_fetch_friends_count(user))
        return Result.taken(extra=extra, media=media, url=url)

    return impersonate_validate(url, process, show_url=url)


def _profile_section(html_text: str) -> str | None:
    match = re.search(
        r'(<section id="spr".*?itemtype="http://schema\.org/Person">.*)', html_text, re.DOTALL
    )
    return match.group(1) if match else None


def _nick(profile: str) -> str:
    match = re.search(r'<h1 class="nick" itemprop="name">(.*?)</h1>', profile, re.DOTALL)
    return _text(match.group(1)) if match else ""


def _extract_profile(profile: str, nick: str) -> tuple[dict, dict]:
    extra: dict = {"name": nick}
    media: dict = {}

    channel_id = re.search(r'<section id="spr" data-channel-id="(\d+)"', profile)
    if channel_id:
        extra["channel_id"] = channel_id.group(1)

    # The badge row renders the visible count rounded ("5.5k"); data-canonical
    # holds the exact figure.
    subscribers = re.search(
        r'class="cm-value subscriber-count"[^>]*data-canonical="(\d+)"', profile
    )
    if subscribers:
        extra["subscribers"] = subscribers.group(1)

    badges = re.findall(r'class="pc-badge pc-[^"]*"\s*title="([^"]+)"', profile)
    if badges:
        extra["badges"] = ", ".join(badges)

    for key, prop in (("birthdate", "birthDate"), ("gender", "gender")):
        meta = re.search(rf'<meta itemprop="{prop}" content="([^"]*)"', profile)
        if meta:
            extra[key] = meta.group(1)

    for label, value in re.findall(
        r'<div class="row">\s*<span class="label">(.*?)</span>\s*<span class="value[^"]*">(.*?)</span>',
        profile,
        re.DOTALL,
    ):
        extra[_text(label)] = _text(value)

    interests = re.search(r'<div itemprop="description">(.*?)</div>', profile, re.DOTALL)
    if interests:
        extra["interests"] = _text(interests.group(1))

    comments = re.search(
        r'<div class="section-title">Comments:</div>(.*?)</div>', profile, re.DOTALL
    )
    if comments:
        extra["comments"] = _text(comments.group(1))

    avatar = re.search(
        r'<a href="([^"]+)">\s*<div class="profile-image-wrapper">\s*'
        r'<img src="([^"]+)"[^>]*class="profile-image"',
        profile,
        re.DOTALL,
    )
    if avatar:
        media["avatar"] = avatar.group(2)
        media["avatar_full"] = avatar.group(1)

    return extra, media


def _fetch_friends_count(user: str) -> dict:
    """The friends tab is the only page exposing the exact friend total."""
    try:
        response = impersonate_request(f"{BASE_URL}/profile/{user}/friends")
    except Exception:
        return {}

    if response.status_code != 200:
        return {}

    count = re.search(r'<li class="page item-count">(\d+)\s+items</li>', response.text)
    return {"friends": count.group(1)} if count else {}


def _text(html_fragment: str) -> str:
    return re.sub(
        r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", html_fragment)).replace("\xa0", " ")
    ).strip()
