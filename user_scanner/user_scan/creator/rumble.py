import html
import json
import re
from urllib.parse import quote

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result

CANONICAL_RE = re.compile(r"<link rel=canonical href=([^\s>]+)>", re.IGNORECASE)
DESCRIPTION_RE = re.compile(
    r'<div class="channel-about--description">.*?<p>(.*?)</p>',
    re.IGNORECASE | re.DOTALL,
)
FOLLOWERS_RE = re.compile(
    r"<span>\s*([\d.,]+[KMB]?)\s+Followers?\s*</span>", re.IGNORECASE
)
IMAGE_RE = re.compile(
    r'class="channel-header--(img|backsplash-img)"[^>]+src="([^"]+)"',
    re.IGNORECASE,
)
NOT_FOUND_MARKERS = {
    404: "<title>404 Not found</title>",
    410: "<title>410 Gone</title>",
}
SOCIAL_RE = re.compile(r'<a href="([^"]+)" class="channel-subheader--socials-item"')
STAT_RE = re.compile(r"([\d,]+)\s+(views|videos)\s*</p>", re.IGNORECASE)
VERIFIED_RE = re.compile(r'<svg class="channel-header--verified\b')


def validate_rumble(user: str) -> Result:
    """Validate a Rumble user account."""
    url = f"https://rumble.com/user/{quote(user, safe='')}"

    def process(response):
        marker = NOT_FOUND_MARKERS.get(response.status_code)
        if marker and marker in response.text:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        canonical = CANONICAL_RE.search(response.text)
        creator_id = re.search(r'"creator_id":\s*"(\d+)"', response.text)
        if (
            not canonical
            or canonical.group(1).casefold() != str(response.url).casefold()
            or not creator_id
        ):
            return Result.error("Rumble user markers do not match the response")

        extra = {"creator_id": creator_id.group(1)}

        profile = {}
        profile_start = re.search(
            rf'\{{"type":"user","url":"{re.escape(canonical.group(1))}"',
            response.text,
            re.IGNORECASE,
        )
        if profile_start:
            try:
                profile = json.JSONDecoder().raw_decode(
                    response.text[profile_start.start() :]
                )[0]
            except json.JSONDecodeError:
                pass

        for field in ("followers", "subscribers"):
            if isinstance(profile.get(field), int):
                extra[field] = profile[field]
        if "followers" not in extra and (followers := FOLLOWERS_RE.search(response.text)):
            value = followers.group(1).replace(",", "")
            extra["followers"] = int(value) if value.isdigit() else value
        extra["verified"] = profile.get(
            "verified_badge", bool(VERIFIED_RE.search(response.text))
        )
        if badge_type := profile.get("badge_type"):
            extra["badge_type"] = badge_type
        if social_links := SOCIAL_RE.findall(response.text):
            extra["social_links"] = [html.unescape(link) for link in social_links]

        try:
            about_response = impersonate_request(f"{url}/about")
        except RequestException:
            about_response = None
        if about_response is not None and about_response.status_code == 200:
            if description := DESCRIPTION_RE.search(about_response.text):
                extra["description"] = " ".join(
                    html.unescape(re.sub(r"<[^>]+>", " ", description.group(1))).split()
                )
            if joined := re.search(r"Joined\s+([^<]+)", about_response.text):
                extra["joined"] = joined.group(1).strip()
            for value, field in STAT_RE.findall(about_response.text):
                extra[field.lower()] = int(value.replace(",", ""))

        media = {
            "avatar" if kind == "img" else "banner": html.unescape(image_url)
            for kind, image_url in IMAGE_RE.findall(response.text)
        }

        return Result.taken(extra=extra, media=media)

    return impersonate_validate(url, process, allow_redirects=True)
