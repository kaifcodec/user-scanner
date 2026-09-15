import html
import json
import re
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def _text(markup: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", markup)).split())


def _extract_profile(response_text: str, profile: dict) -> tuple[dict, dict]:
    extra = {
        "username": str(profile.get("identifier", "")).removeprefix("@"),
        "display_name": profile.get("name"),
        "bio": profile.get("description"),
    }
    media = {"avatar": profile.get("image")}

    description_match = re.search(
        r'<meta\s[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']*)',
        response_text,
        re.IGNORECASE,
    )
    stats_text = html.unescape(description_match.group(1)) if description_match else ""
    if rank_match := re.search(r"Ранг:\s*([^\.]+)", stats_text):
        extra["rank"] = rank_match.group(1).strip()
    if followers_match := re.search(r"Подписчики:\s*(\d+)", stats_text):
        extra["followers"] = int(followers_match.group(1))
    if following_match := re.search(
        r'href="[^"]+/follows">\s*<span[^>]*>(\d+)</span>',
        response_text,
    ):
        extra["following"] = int(following_match.group(1))

    if user_id_match := re.search(
        r'<div\s+wire:key="(\d+)"[^>]*wire:name="profile"', response_text
    ):
        extra["user_id"] = int(user_id_match.group(1))

    if demographics_match := re.search(
        r"<div\b(?=[^>]*\bdata-profile-demographics\b)[^>]*>(.*?)</div>\s*</div>",
        response_text,
        re.DOTALL,
    ):
        demographics = _text(demographics_match.group(1))
        if match := re.fullmatch(r"(.+?)(?:\s+(\d+))?\s*•\s*(\S+)", demographics):
            extra["gender"] = match.group(1)
            extra["age"] = int(match.group(2)) if match.group(2) else None
            extra["region"] = match.group(3)

    identity_match = re.search(
        r"data-profile-name-row\b[^>]*>.*?</h1>", response_text, re.DOTALL
    )
    extra["verified"] = bool(identity_match and "<svg" in identity_match.group(0))

    if badge_match := re.search(
        r"<button\b(?=[^>]*\bdata-profile-badge\b)[^>]*>(.*?)</button>",
        response_text,
        re.DOTALL,
    ):
        extra["badge"] = _text(badge_match.group(1))

    if (
        website_tag := re.search(
            r"<a\b(?=[^>]*\bdata-profile-website\b)[^>]*>", response_text
        )
    ) and (href_match := re.search(r'href=["\']([^"\']+)', website_tag.group(0))):
        extra["website"] = html.unescape(href_match.group(1)).removeprefix(
            "https://stackb.net/redirect/"
        )

    if games := [
        _text(match)
        for match in re.findall(
            r"<a\b(?=[^>]*class=[\"\'][^\"\']*\bgame-card\b)[^>]*>(.*?)</a>",
            response_text,
            re.DOTALL,
        )
    ]:
        extra["games"] = games

    if cover_tag := re.search(
        r"<div\b(?=[^>]*\bdata-profile-cover\b)[^>]*>", response_text
    ):
        decoded_tag = html.unescape(cover_tag.group(0))
        if cover_match := re.search(
            r"background-image:\s*url\(['\"]?([^'\")]+)", decoded_tag
        ):
            media["banner"] = cover_match.group(1)

    return extra, media


def validate_stackb(user: str) -> Result:
    url = f"https://stackb.net/@{quote(user, safe='')}"
    show_url = f"https://stackb.net/@{user}"

    def process(response):
        if response.status_code == 404 and "Ошибка 404" in response.text:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected profile status: {response.status_code}")

        match = re.search(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            response.text,
            re.DOTALL,
        )
        data = json.loads(html.unescape(match.group(1))) if match else {}
        profile = data.get("mainEntity") if data.get("@type") == "ProfilePage" else None
        if isinstance(profile, dict) and profile.get("@type") == "Person":
            extra, media = _extract_profile(response.text, profile)
            return Result.taken(extra=extra, media=media)

        return Result.error("Unexpected profile response")

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
