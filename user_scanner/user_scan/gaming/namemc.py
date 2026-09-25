from __future__ import annotations

import html
import re
from datetime import datetime
from urllib.parse import urljoin

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

SHOW_URL = "https://namemc.com"
SEARCH_URL = "https://namemc.com/search"

_CARD_RE = re.compile(
    r'<div class="card mb-3">(.*?)</table>\s*</div>\s*</div>',
    re.DOTALL,
)
_PROFILE_LINK_RE = re.compile(
    r'<h3 class="mb-0"[^>]*>\s*<a href="([^"]+)">\s*([^<]+?)\s*</a>',
    re.DOTALL,
)
_AVATAR_RE = re.compile(r'<img class="skin-2d[^"]*"[^>]+src="([^"]+)"')
_ROW_RE = re.compile(r'<tr class="([^"]*)">(.*?)</tr>', re.DOTALL)
_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
_TIME_RE = re.compile(r'<time[^>]+datetime="([^"]+)"')


def _text(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def _extract_profiles(page: str) -> list[dict]:
    profiles = []

    for card in _CARD_RE.findall(page):
        link_match = _PROFILE_LINK_RE.search(card)
        if not link_match:
            continue

        profile_href = urljoin(SHOW_URL, link_match.group(1))
        profile_name = _text(link_match.group(2))

        entries = []
        for row_class, row_html in _ROW_RE.findall(card):
            if "d-lg-none" in row_class:
                continue

            cells = _TD_RE.findall(row_html)
            if len(cells) < 2:
                continue

            name_text = _text(cells[1])
            if name_text in ("", "\u2014"):
                name_text = profile_name

            time_match = _TIME_RE.search(row_html)
            changed_at = time_match.group(1) if time_match else None

            entries.append({"name": name_text, "changed_at": changed_at})

        avatar_match = _AVATAR_RE.search(card)
        avatar = urljoin(SHOW_URL, html.unescape(avatar_match.group(1))) if avatar_match else None

        profiles.append({
            "name": profile_name,
            "url": profile_href,
            "history": entries,
            "avatar": avatar,
        })

    return profiles


def _format_datetime(iso_str: str | None) -> str:
    if not iso_str:
        return "account creation"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return iso_str


def _format_history(profiles: list[dict]) -> str:
    multi = len(profiles) > 1
    blocks = []

    for i, profile in enumerate(profiles, start=1):
        header = f"{profile['name']} -- {profile['url']}"
        if multi:
            header = f"Profile {i}: {header}"

        lines = [header]
        if profile["history"]:
            for j, entry in enumerate(profile["history"], start=1):
                when = _format_datetime(entry["changed_at"])
                lines.append(f"  {j}. {entry['name']} ({when})")
        else:
            lines.append("  (no name history)")

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def process(response) -> Result:
    if response.status_code != 200:
        return Result.error(f"Unexpected status code {response.status_code}")

    profiles = _extract_profiles(response.text)

    if profiles:
        extra = {"history": _format_history(profiles)}
        media = {}
        first_avatar = next((p["avatar"] for p in profiles if p["avatar"]), None)
        if first_avatar:
            media["avatar"] = first_avatar

        return Result.taken(extra=extra, media=media or None)

    return Result.available()


def validate_namemc(user: str) -> Result:
    return impersonate_validate(
        SEARCH_URL,
        process,
        params={"q": user},
        warmup_url=SHOW_URL,
        impersonate="chrome",
        show_url=f"{SHOW_URL}/search?q={user}",
        allow_redirects=True,
    )
