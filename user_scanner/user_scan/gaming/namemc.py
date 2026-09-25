from __future__ import annotations

from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

SHOW_URL = "https://namemc.com"
SEARCH_URL = "https://namemc.com/search"


def _extract_profiles(soup: BeautifulSoup) -> list:
    profiles = []

    for card in soup.select("div.card.mb-3"):
        link_tag = card.select_one("h3.mb-0 a")
        if not link_tag:
            continue

        profile_name = link_tag.get_text(strip=True)
        profile_href = urljoin(SHOW_URL, link_tag.get("href", ""))

        rows = [
            row for row in card.select("table.name-list tbody tr")
            if "d-lg-none" not in (row.get("class") or [])
        ]

        entries = []
        for row in rows:
            tds = row.find_all("td")
            if len(tds) < 2:
                continue

            name_text = tds[1].get_text(strip=True)
            if name_text in ("", "\u2014"):
                name_text = profile_name

            time_tag = row.find("time")
            changed_at = time_tag["datetime"] if time_tag and time_tag.get("datetime") else None

            entries.append({"name": name_text, "changed_at": changed_at})

        profiles.append({
            "name": profile_name,
            "url": profile_href,
            "history": entries,
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


def _format_history(profiles: list) -> str:
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

    soup = BeautifulSoup(response.text, "html.parser")
    meta = soup.find("meta", attrs={"name": "description"})
    meta_content = meta.get("content", "") if meta else ""
    availability_time = soup.find("time", id="availability-time")

    profiles = _extract_profiles(soup)

    if availability_time is not None or "Status: Available" in meta_content:
        extra = {}
        if profiles:
            extra["history"] = _format_history(profiles)
        return Result.available(extra=extra or None)

    if "Status: Taken" in meta_content or profiles:
        extra = {}
        if profiles:
            extra["history"] = _format_history(profiles)
        else:
            extra["history"] = "Could not extract name history"

        media = {}
        avatar = soup.select_one(".card-body img, img.card-img")
        if avatar and avatar.get("src"):
            media["avatar"] = urljoin(SHOW_URL, avatar["src"])

        return Result.taken(extra=extra or None, media=media or None)

    if not profiles and "Status:" not in meta_content:
        return Result.error("Could not determine name status")

    return Result.error("Could not determine name status from response")


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
