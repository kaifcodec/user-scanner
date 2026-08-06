import hashlib
import html
import re

import httpx

from user_scanner.core.helpers import get_global_timeout
from user_scanner.core.result import Result

PROFILE_HOST = "https://gravatar.com"
DEFAULT_TIMEOUT = 15.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# The public JSON APIs omit the profile's "Links" card, its interests and the
# advanced-details panel; only the rendered profile page carries them.
LINKS_SECTION_RE = re.compile(
    r'g-profile__links".*?(?=<div class="g-profile__card|<button class="g-profile__adv-details-btn)',
    re.S,
)
LINK_RE = re.compile(r'<a class="card-item__link"\s+href="([^"]+)"\s+title="([^"]*)"', re.S)
INTERESTS_RE = re.compile(r'g-profile__interests-list">(.*?)</ul>', re.S)
INTEREST_ITEM_RE = re.compile(r"<span>\s*([^<]+?)\s*</span>")
ADV_DETAIL_RE = re.compile(
    r"<span>\s*(Profile|Updated|Created|Languages|Time):\s*([^<]+?)\s*</span>"
)
# Both JSON APIs list only the providers their schema knows about — a YouTube
# connection is absent from each yet rendered on the page, so the card is the
# only complete source.
VERIFIED_SECTION_RE = re.compile(
    r'g-profile__card is-verified-accounts".*?(?=<div class="g-profile__card|\Z)', re.S
)
VERIFIED_ITEM_RE = re.compile(
    r'card-item__label-text">\s*([^<]+?)\s*</span>.*?class="card-item__link"\s+href="([^"]+)"',
    re.S,
)
TIMEZONE_RE = re.compile(r"\(([^)]+)\)")

# The markdown export spells out what the profile page abbreviates: full
# language names with primary/secondary, and an IANA zone instead of a
# DST-dependent UTC offset.
MARKDOWN_KEYS = {
    "Languages": "languages",
    "Timezone": "timezone",
}

ADV_DETAIL_KEYS = {
    "Profile": "profile_type",
    "Updated": "last_updated",
    "Created": "created",
    "Languages": "languages",
}


async def validate_gravatar(email: str) -> Result:
    email_clean = email.lower().strip()
    timeout = get_global_timeout() or DEFAULT_TIMEOUT
    # Older profiles are only addressable by the legacy MD5 hash.
    hashes = [
        hashlib.sha256(email_clean.encode("utf-8")).hexdigest(),
        hashlib.md5(email_clean.encode("utf-8")).hexdigest(),
    ]
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            for email_hash in hashes:
                response = await client.get(
                    f"https://www.gravatar.com/avatar/{email_hash}?d=404", headers=HEADERS
                )
                if response.status_code == 200:
                    extra, media = await _collect_profile(client, email_hash)
                    return Result.taken(
                        url=extra.get("profile_url", PROFILE_HOST), extra=extra, media=media
                    )
                if response.status_code != 404:
                    return Result.error(f"HTTP {response.status_code}", url=PROFILE_HOST)
            return Result.available(url=PROFILE_HOST)
    except httpx.TimeoutException:
        return Result.error("Connection timed out", url=PROFILE_HOST)
    except Exception as e:
        return Result.error(e, url=PROFILE_HOST)


async def _collect_profile(client: httpx.AsyncClient, email_hash: str) -> tuple[dict, dict]:
    extra: dict = {}
    media: dict = {"avatar": f"https://www.gravatar.com/avatar/{email_hash}"}
    try:
        response = await client.get(f"https://en.gravatar.com/{email_hash}.json", headers=HEADERS)
        if response.status_code == 200:
            entries = response.json().get("entry") or []
            if entries and isinstance(entries[0], dict):
                _extract_profile_data(entries[0], extra, media)
    except Exception:
        pass
    try:
        response = await client.get(f"{PROFILE_HOST}/{email_hash}", headers=HEADERS)
        if response.status_code == 200:
            _extract_page_data(response.text, extra)
    except Exception:
        pass
    try:
        response = await client.get(f"{PROFILE_HOST}/{email_hash}.md", headers=HEADERS)
        if response.status_code == 200:
            _extract_markdown_data(response.text, extra)
    except Exception:
        pass
    return extra, media


def _extract_profile_data(entry: dict, extra: dict, media: dict) -> None:
    if entry.get("preferredUsername"):
        extra["username"] = str(entry["preferredUsername"]).strip()
    if entry.get("displayName"):
        extra["display_name"] = str(entry["displayName"]).strip()
    if entry.get("profileUrl"):
        extra["profile_url"] = str(entry["profileUrl"]).strip()
    if entry.get("thumbnailUrl"):
        media["thumbnail_url"] = str(entry["thumbnailUrl"]).strip()
    if entry.get("aboutMe"):
        extra["bio"] = str(entry["aboutMe"]).strip()
    if entry.get("currentLocation"):
        extra["location"] = str(entry["currentLocation"]).strip()
    # The legacy endpoint returns this as job_title; jobTitle is the v3 spelling.
    job_title = entry.get("jobTitle") or entry.get("job_title")
    if job_title:
        extra["job_title"] = str(job_title).strip()
    if entry.get("company"):
        extra["company"] = str(entry["company"]).strip()
    if entry.get("pronouns"):
        extra["pronouns"] = str(entry["pronouns"]).strip()
    if entry.get("pronunciation"):
        extra["pronunciation"] = str(entry["pronunciation"]).strip()

    name_info = entry.get("name")
    if isinstance(name_info, dict) and name_info.get("formatted"):
        extra["full_name"] = str(name_info["formatted"]).strip()

    photos = entry.get("photos")
    if isinstance(photos, list):
        photo_list = [
            str(p["value"]).strip()
            for p in photos
            if isinstance(p, dict) and p.get("value") is not None and str(p["value"]).strip()
        ]
        if photo_list:
            media["photos"] = ", ".join(photo_list)

    accounts = entry.get("accounts")
    if isinstance(accounts, list):
        acc_list = []
        for acc in accounts:
            if not isinstance(acc, dict):
                continue
            acc_name = str(acc.get("name") or acc.get("shortname") or "Account")
            acc_url = acc.get("url") or acc.get("display") or acc.get("username")
            if acc_url is not None and str(acc_url).strip():
                status = " (verified)" if acc.get("verified") else ""
                acc_list.append(f"{acc_name}: {str(acc_url).strip()}{status}")
        if acc_list:
            extra["verified_accounts"] = ", ".join(acc_list)

    urls = entry.get("urls")
    if isinstance(urls, list):
        url_list = [
            str(u["value"]).strip()
            for u in urls
            if isinstance(u, dict) and u.get("value") is not None and str(u["value"]).strip()
        ]
        if url_list:
            extra["websites"] = ", ".join(url_list)

    contact_info = entry.get("contactInfo")
    if isinstance(contact_info, list):
        contact_list = [
            f"{str(c.get('type', 'contact'))}: {str(c['value']).strip()}"
            for c in contact_info
            if isinstance(c, dict) and c.get("value") is not None and str(c["value"]).strip()
        ]
        if contact_list:
            extra["contact_info"] = ", ".join(contact_list)

    phones = entry.get("phoneNumbers")
    if isinstance(phones, list):
        phone_list = [
            f"{str(p.get('type', 'phone'))}: {str(p['value']).strip()}"
            for p in phones
            if isinstance(p, dict) and p.get("value") is not None and str(p["value"]).strip()
        ]
        if phone_list:
            extra["phone_numbers"] = ", ".join(phone_list)

    emails = entry.get("emails")
    if isinstance(emails, list):
        email_list = [
            str(e["value"]).strip()
            for e in emails
            if isinstance(e, dict) and e.get("value") is not None and str(e["value"]).strip()
        ]
        if email_list:
            extra["public_emails"] = ", ".join(email_list)

    crypto = entry.get("crypto")
    if isinstance(crypto, list):
        crypto_list = [
            f"{str(c.get('currency', 'Wallet'))}: {str(c['value']).strip()}"
            for c in crypto
            if isinstance(c, dict) and c.get("value") is not None and str(c["value"]).strip()
        ]
        if crypto_list:
            extra["crypto_addresses"] = ", ".join(crypto_list)

    background = entry.get("profileBackground")
    if isinstance(background, dict):
        if background.get("url"):
            media["background"] = str(background["url"]).strip()
        if background.get("color"):
            extra["background_color"] = str(background["color"]).strip()


def _extract_page_data(page: str, extra: dict) -> None:
    _merge_verified_accounts(page, extra)

    section = LINKS_SECTION_RE.search(page)
    if section:
        links = []
        for url, title in LINK_RE.findall(section.group(0)):
            url = html.unescape(url).strip()
            title = html.unescape(title).strip()
            if not url:
                continue
            links.append(f"{title}: {url}" if title and title != url else url)
        if links:
            extra["links"] = ", ".join(links)

    interests = INTERESTS_RE.search(page)
    if interests:
        items = [html.unescape(i).strip() for i in INTEREST_ITEM_RE.findall(interests.group(1))]
        items = [i for i in items if i]
        if items:
            extra["interests"] = ", ".join(items)

    for label, value in ADV_DETAIL_RE.findall(page):
        value = html.unescape(value).strip()
        if not value or value == "-":
            continue
        if label == "Time":
            zone = TIMEZONE_RE.search(value)
            # Profiles with no timezone set render as UTC, so a bare "UTC" says
            # nothing about the owner and is dropped.
            if zone and zone.group(1).strip() != "UTC":
                extra["timezone"] = zone.group(1).strip()
            continue
        extra[ADV_DETAIL_KEYS[label]] = value


def _merge_verified_accounts(page: str, extra: dict) -> None:
    section = VERIFIED_SECTION_RE.search(page)
    if not section:
        return

    existing = [e for e in str(extra.get("verified_accounts", "")).split(", ") if e]
    known = {_normalize_url(e.rsplit(": ", 1)[-1]) for e in existing}
    for label, url in VERIFIED_ITEM_RE.findall(section.group(0)):
        label = html.unescape(label).strip()
        url = html.unescape(url).strip()
        if not url or _normalize_url(url) in known:
            continue
        known.add(_normalize_url(url))
        existing.append(f"{label or 'Account'}: {url} (verified)")
    if existing:
        extra["verified_accounts"] = ", ".join(existing)


def _extract_markdown_data(page: str, extra: dict) -> None:
    for label, key in MARKDOWN_KEYS.items():
        match = re.search(rf"^- {label}: (.+)$", page, re.M)
        if not match:
            continue
        # Markdown-escapes any punctuation, e.g. America/Sao\_Paulo.
        value = re.sub(r"\\(.)", r"\1", match.group(1)).strip()
        if value:
            extra[key] = value


def _normalize_url(value: str) -> str:
    return value.removesuffix(" (verified)").strip().rstrip("/").lower()
