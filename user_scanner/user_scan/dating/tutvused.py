import html
import re
from urllib.parse import quote, unquote, urlsplit

import httpx

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_tutvused(user: str) -> Result:
    username = user.strip()
    url = f"https://tutvused.net/vendor/{quote(username, safe='')}/"

    def process(response: httpx.Response) -> Result:
        if (
            "<title>One moment, please...</title>" in response.text
            and "Please wait while your request is being verified..." in response.text
        ):
            return Result.error("Blocked by Tutvused bot challenge")
        if (
            response.status_code == 404
            and "<title>Page not found - Tutvused</title>" in response.text
        ):
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        canonical = re.search(
            r"https://tutvused\.net/vendor/([^/\"'?]+)/", response.text
        )
        profile = re.search(
            r'<aside[^>]+class="[^"]*hp-vendor--view-page[^"]*".*?</aside>',
            response.text,
            re.DOTALL,
        )
        if not canonical or not profile:
            return Result.error("Could not verify profile page")
        if unquote(canonical.group(1)).casefold() != username.casefold():
            return Result.error("Profile response does not match the requested handle")

        extra: dict[str, object] = {}
        listing_count = len(
            re.findall(r'<article class="[^"]*hp-listing--view-block', response.text)
        )
        if listing_count:
            extra["listing_count"] = listing_count
        if name := re.search(
            r'<h3 class="hp-vendor__name">.*?<span>(.*?)</span>\s*</h3>',
            response.text,
            re.DOTALL,
        ):
            extra["name"] = _text(name.group(1))
        if joined := re.search(
            r'<time class="[^"]*hp-vendor__registered-date[^"]*"\s+'
            r'datetime="([^"]+)"',
            response.text,
        ):
            extra["joined"] = joined.group(1)
        if description := re.search(
            r'<div class="hp-vendor__description">(.*?)</div>',
            response.text,
            re.DOTALL,
        ):
            extra["bio"] = _text(description.group(1))
        if last_seen := re.search(
            r'class="hp-vendor__online-badge[^"]*"\s+title="Last seen ([^"]+)"',
            response.text,
        ):
            extra["last_seen"] = html.unescape(last_seen.group(1)).strip()
        if links := _external_links(profile.group(0)):
            extra["links"] = links

        avatar = re.search(
            r'<div class="hp-vendor__image">\s*<img[^>]+src="([^"]+)"',
            response.text,
        )
        media = (
            {"avatar": html.unescape(avatar.group(1))}
            if avatar and "/placeholders/" not in avatar.group(1)
            else {}
        )
        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=url)


def _external_links(profile: str) -> list[str]:
    links: list[str] = []
    for raw_url in re.findall(r'<a[^>]+href=["\']([^"\']+)', profile):
        url = html.unescape(raw_url).strip()
        parsed = urlsplit(url)
        host = (parsed.hostname or "").removeprefix("www.")
        if parsed.scheme not in {"http", "https", "mailto", "tel"}:
            continue
        if parsed.scheme in {"http", "https"} and (
            host == "tutvused.net" or host.endswith(".tutvused.net")
        ):
            continue
        if url not in links:
            links.append(url)
    return links


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()
