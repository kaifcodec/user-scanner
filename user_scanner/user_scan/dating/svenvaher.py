import html
import re
from urllib.parse import quote

import httpx

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

PROFILE_FIELDS = {
    "Orientatsioon": "orientation",
    "Pikkus cm": "height_cm",
    "Kaal kg": "weight_kg",
    "Turvaline seks?": "safe_sex",
    "Otsin": "looking_for",
    "Vanusevahemikus": "desired_age",
    "Avalik e-mail": "public_email",
}


def validate_svenvaher(user: str) -> Result:
    username = user.strip()
    url = f"https://svenvaher.ee/{quote(username, safe='')}"

    def process(response: httpx.Response) -> Result:
        if (
            response.status_code == 403
            and "<title>Attention Required! | Cloudflare</title>" in response.text
            and "Sorry, you have been blocked" in response.text
        ):
            return Result.error("Blocked by SvenVaher Cloudflare security")
        if (
            response.status_code == 404
            and "<title>404 Ei leitud</title>" in response.text
        ):
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        match = re.search(
            r'<div class="profile-name-wrapper">\s*<a[^>]*>(.*?)</a>',
            response.text,
            re.DOTALL,
        )
        if not match:
            return Result.error("Could not verify profile page")

        profile_user = _text(match.group(1))
        if profile_user.casefold() != username.casefold():
            return Result.error("Profile response does not match the requested handle")

        extra = _about(response.text)

        stat_names = {"Postitused": "posts", "Fotod": "photos", "Videod": "videos"}
        for count, label in re.findall(
            r"(\d+)\s+(Postitused|Fotod|Videod)", response.text
        ):
            extra[stat_names[label]] = int(count)

        avatar = re.search(
            r'<div class="profile-avatar-wrapper">\s*'
            r'<img[^>]+\bdata-image="([^"]+)"',
            response.text,
        )
        media: dict[str, str] = {}
        if avatar:
            media["avatar"] = html.unescape(avatar.group(1))
        if cover := re.search(
            r'<div class="profile-cover-wrapper">.*?'
            r'<img class="js_position-cover-full[^"]*" src="([^"]+)"',
            response.text,
            re.DOTALL,
        ):
            media["cover"] = html.unescape(cover.group(1))
        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=url)


def _about(page: str) -> dict[str, object]:
    extra: dict[str, object] = {}
    if bio := re.search(
        r'<div class="about-bio">.*?'
        r'<div class="js_readmore[^"]*">(.*?)</div>',
        page,
        re.DOTALL,
    ):
        extra["bio"] = _text(bio.group(1))

    about = re.search(r'<ul class="about-list">(.*?)</ul>', page, re.DOTALL)
    if about:
        items = re.findall(
            r'<div class="about-list-item">(.*?)</div>\s*</li>',
            about.group(1),
            re.DOTALL,
        )
        relationships = {
            "Üksik",
            "Suhtes",
            "Abielus",
            "See on keeruline",
            "Lahus",
            "Lahutatud",
            "Lesk",
        }
        for raw_item in items:
            item = _text(raw_item)
            if item.startswith("Elab "):
                extra["location"] = item.removeprefix("Elab ")
            elif item.startswith("Pärit "):
                extra["hometown"] = item.removeprefix("Pärit ")
            elif item in {"Mees", "Naine", "Muu"}:
                extra["gender"] = item
            elif item in relationships:
                extra["relationship_status"] = item
            elif birth_date := re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", item):
                extra["birth_date"] = "-".join(reversed(birth_date.groups()))
            elif followers := re.fullmatch(r"Jälgib\s+(\d+)\s+inimes(?:t|ed)", item):
                extra["followers"] = int(followers.group(1))

    for raw_label, raw_value in re.findall(
        r"<li>\s*<strong>(.*?)</strong><br>(.*?)</li>", page, re.DOTALL
    ):
        field = PROFILE_FIELDS.get(_text(raw_label))
        if not field:
            continue
        if field == "public_email":
            if protected := re.search(r'data-cfemail="([0-9a-f]+)"', raw_value):
                extra[field] = _decode_cfemail(protected.group(1))
        elif value := _text(raw_value):
            extra[field] = value

    if pronouns := re.search(
        r'class="profile-pronouns[^"]*">\s*\((.*?)\)\s*</span>', page
    ):
        extra["pronouns"] = _text(pronouns.group(1))
    if 'class="verified-badge"' in page:
        extra["verified"] = True
    return extra


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def _decode_cfemail(value: str) -> str:
    key = int(value[:2], 16)
    return bytes(byte ^ key for byte in bytes.fromhex(value[2:])).decode()
