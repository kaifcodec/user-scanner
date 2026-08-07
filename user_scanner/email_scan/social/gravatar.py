import hashlib
import html
import re
from collections.abc import Iterator

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
INTERESTS_RE = re.compile(r"<h2[^>]*>\s*Interests\s*</h2>.*?<ul[^>]*>(.*?)</ul>", re.S)
INTEREST_ITEM_RE = re.compile(r"<span>\s*([^<]+?)\s*</span>")
TITLE_RE = re.compile(r'title="([^"]*)"')
ADV_DETAIL_RE = re.compile(
    r"<span>\s*(Profile|Updated|Created|Languages|Time):\s*([^<]+?)\s*</span>"
)
# Both JSON APIs list only the providers their schema knows about — a YouTube
# connection is absent from each yet rendered on the page, so the card is the
# only complete source. Each entry is anchored on its checkmark's help link and
# the rel="me" of the account anchor rather than on styling hooks.
VERIFIED_MARKER = "support.gravatar.com/profiles/verified-accounts"
VERIFIED_LABEL_RE = re.compile(r">\s*([^<>]{1,60}?)\s*</span>\s*<a[^>]*$", re.S)
ANCHOR_RE = re.compile(r"<a\b[^>]*>", re.S)
REL_ME_RE = re.compile(r'rel="[^"]*\bme\b[^"]*"')
HREF_RE = re.compile(r'href="([^"]+)"')
TIMEZONE_RE = re.compile(r"\(([^)]+)\)")

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
            acc_url = str(acc.get("url") or acc.get("display") or acc.get("username") or "").strip()
            status = " (verified)" if acc.get("verified") else ""
            # Providers that forbid public profile links (Facebook) are stored
            # pointing at Gravatar's help page, which says nothing about the user.
            if VERIFIED_MARKER in acc_url:
                acc_url = ""
            if acc_url:
                acc_list.append(f"{acc_name}: {acc_url}{status}")
            elif acc.get("verified"):
                acc_list.append(f"{acc_name}{status}")
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

    links = []
    for title, url in _iter_links(page):
        entry = f"{title}: {url}"
        if entry not in links:
            links.append(entry)
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
    existing = [e for e in str(extra.get("verified_accounts", "")).split(", ") if e]
    known_urls = {_normalize_url(e.rsplit(": ", 1)[-1]) for e in existing}
    # The same account can carry different URLs in each source — the JSON keeps
    # whatever the owner entered, the page renders a canonical one — so the
    # service name is what identifies a duplicate.
    known_services = {e.split(":", 1)[0].removesuffix(" (verified)").strip().lower() for e in existing}
    for label, url in _iter_verified_accounts(page):
        if _normalize_url(url) in known_urls or label.lower() in known_services:
            continue
        known_urls.add(_normalize_url(url))
        known_services.add(label.lower())
        existing.append(f"{label or 'Account'}: {url} (verified)")
    if existing:
        extra["verified_accounts"] = ", ".join(existing)


def _iter_verified_accounts(page: str) -> Iterator[tuple[str, str]]:
    markers = [m.start() for m in re.finditer(re.escape(VERIFIED_MARKER), page)]
    for index, start in enumerate(markers):
        # The account anchor sits between this checkmark and the next entry's.
        end = markers[index + 1] if index + 1 < len(markers) else len(page)
        url = ""
        for tag in ANCHOR_RE.finditer(page, start, end):
            href = HREF_RE.search(tag.group(0))
            if href and REL_ME_RE.search(tag.group(0)):
                url = html.unescape(href.group(1)).strip()
                break
        # A help-page URL is the placeholder for providers that forbid public
        # links, and it also matches the marker, so it seeds phantom entries.
        if not url or VERIFIED_MARKER in url:
            continue
        label = VERIFIED_LABEL_RE.search(page, max(0, start - 300), start)
        yield (html.unescape(label.group(1)).strip() if label else ""), url


def _iter_links(page: str) -> Iterator[tuple[str, str]]:
    # A personal link carries the owner's own caption; every other rel="me"
    # anchor on the page — the icon row and the verified cards — repeats its own
    # URL as the title.
    for tag in ANCHOR_RE.finditer(page):
        if not REL_ME_RE.search(tag.group(0)):
            continue
        href = HREF_RE.search(tag.group(0))
        title = TITLE_RE.search(tag.group(0))
        if not href or not title:
            continue
        url = html.unescape(href.group(1)).strip()
        caption = html.unescape(title.group(1)).strip()
        if url and caption and caption != url:
            yield caption, url


def _normalize_url(value: str) -> str:
    return value.removesuffix(" (verified)").strip().rstrip("/").lower()
