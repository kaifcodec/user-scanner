import html
import json
import re
from decimal import Decimal
from urllib.parse import quote, unquote, urlsplit

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

NOT_FOUND = "The page you were looking for doesn’t exist (404 Not found)"


def validate_allpoetry(user: str) -> Result:
    url = f"https://allpoetry.com/{quote(user, safe='')}"

    def process(response):
        document = response.text
        if response.status_code == 404 and NOT_FOUND in document:
            return Result.available()

        person = _person(document)
        canonical = urlsplit(str(person.get("url", "")))
        handle = unquote(canonical.path.strip("/"))
        if (
            response.status_code == 200
            and canonical.hostname == "allpoetry.com"
            and handle.casefold() == user.casefold()
        ):
            account_type = (
                "curated_poet" if person.get("birthDate") else "member"
            )
            extra = {
                "account_type": account_type,
                "name": person.get("name"),
                "canonical_url": person.get("url"),
                "description": person.get("description"),
                "occupation": person.get("jobTitle"),
                "birth_date": person.get("birthDate"),
                "death_date": person.get("deathDate"),
            }
            extra.update(_profile_details(document, handle, account_type))
            return Result.taken(
                extra=extra,
                media={"avatar": person.get("image")},
            )

        return Result.error(f"Unexpected AllPoetry response: {response.status_code}")

    return generic_validate(url, process, show_url=url, follow_redirects=True)


def _person(document: str) -> dict:
    for block in re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        document,
        re.IGNORECASE | re.DOTALL,
    ):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Person":
            return data
    return {}


def _profile_details(document: str, handle: str, account_type: str) -> dict:
    profile = document.partition('class="itm relative')[0]
    bio_html = _preview_content(profile)
    details: dict[str, str | bool | int | list[str]] = {}
    if bio := _text(bio_html):
        details["bio"] = bio
    if links := _external_links(bio_html):
        details["external_links"] = links

    if account_type == "curated_poet":
        if rank := re.search(r"Ranked\s+#([\d,.]+)", profile, re.IGNORECASE):
            details["famous_rank"] = _number(rank.group(1))
        return details

    headers = [
        match.group(0)
        for match in re.finditer(r"<header\b.*?</header>", document, re.DOTALL)
        if re.search(r"<h1[^>]*\bu_\d+\b", match.group(0))
    ]
    if not headers:
        return details
    header = "".join(headers)

    if user_id := re.search(r"<h1[^>]*\bu_(\d+)\b", header):
        details["user_id"] = int(user_id.group(1))
    if last_seen := re.search(
        r"<abbr[^>]*timeago[^>]*title=(['\"])(.*?)\1[^>]*>", header
    ):
        details["last_seen"] = html.unescape(last_seen.group(2))
        details["online"] = "Currently online" in header or "Online now" in header
    if joined := re.search(
        r"<abbr[^>]*timeago[^>]*>.*?"
        r'<span class="truncate">(\d{4})</span>',
        header,
        re.DOTALL,
    ):
        details["joined_year"] = int(joined.group(1))
    if membership := re.search(r'/images/leaf-([a-z]+)\.png', header):
        details["membership"] = membership.group(1).title()

    link_counts = {
        "comments": r'/comment/by/[^"]+',
        "comments_received": r'/comment/on/[^"]+',
        "followers": rf"/following/{re.escape(handle)}/followed_by",
        "following": rf"/following/{re.escape(handle)}",
    }
    for field, href in link_counts.items():
        if (value := _link_count(header, href)) is not None:
            details[field] = value

    if location := re.search(
        r'<span class="truncate" title="([^"]+)">[^<]*</span>', header
    ):
        details["location"] = html.unescape(location.group(1))

    levels = [
        _text(value)
        for value in re.findall(
            rf'<a[^>]*href="/{re.escape(handle)}/levels"[^>]*>(.*?)</a>',
            document,
            re.DOTALL,
        )
    ]
    if level := next((value for value in levels if value.startswith("Level ")), None):
        details["level"] = level
        if level_number := re.match(r"Level\s+(\d+)", level):
            details["level_number"] = int(level_number.group(1))

    if rank := re.search(r"Rank\s+([^<]+?)\s+lifetime", header):
        rank_text = rank.group(1).strip()
        weekly_rank = re.fullmatch(
            r"([\d,.]+[kKmM]?)/([\d,.]+[kKmM]?) this week,\s*"
            r"([\d,.]+[kKmM]?)",
            rank_text,
        )
        if weekly_rank:
            details["weekly_rank"] = _number(weekly_rank.group(1))
            details["weekly_rank_total"] = _number(weekly_rank.group(2))
            details["lifetime_rank"] = _number(weekly_rank.group(3))
        else:
            details["lifetime_rank"] = _number(rank_text)
    if points := re.search(
        r'<span class="nocolor">Week</span>\s*([^<]+)'
        r'<span class="nocolor">All\s*</span>\s*([^<]+)',
        header,
    ):
        details["weekly_points"], details["lifetime_points"] = (
            _number(points.group(1)),
            _number(points.group(2)),
        )

    for award in re.findall(
        rf'<a[^>]*href="/{re.escape(handle)}/winners"[^>]*>(.*?)</a>',
        header,
        re.DOTALL,
    ):
        title = re.search(r'title="([^"]+)"', award)
        count = re.search(r"<span>([\d,.]+)</span>", award)
        if title and count:
            details[f"wins_{title.group(1).casefold()}"] = _number(count.group(1))

    if (picks := _link_count(
        header, rf"/picks/pick_by/{re.escape(handle)}"
    )) is not None:
        details["front_page_picks"] = picks

    for kind, content in re.findall(
        rf'<a[^>]*href="/{re.escape(handle)}\?kind=(\w+)(?:&|&amp;)tab=recent"'
        rf"[^>]*>(.*?)</a>",
        document,
        re.DOTALL,
    ):
        if count := re.search(r"\(([\d,.]+)\)", _text(content)):
            field = {"story": "stories"}.get(kind, f"{kind}s")
            details[field] = _number(count.group(1))

    group_area = re.search(
        r'id="mobile_user_groups_list".*?<div class="books_target',
        header,
        re.DOTALL,
    )
    if group_area:
        groups = [
            name
            for value in re.findall(
                r'<a[^>]*href="/groups/\d+"[^>]*>(.*?)</a>',
                group_area.group(0),
                re.DOTALL,
            )
            if (name := _text(value))
        ]
        if groups:
            details["active_groups"] = groups

    books = [
        book_title
        for value in re.findall(
            r'<a[^>]*href="/books/\d+"[^>]*>.*?'
            r'<div class="leading-tight[^"]*">(.*?)</div>',
            document,
            re.DOTALL,
        )
        if (book_title := _text(value))
    ]
    if books:
        details["books"] = books
    return details


def _preview_content(document: str) -> str:
    match = re.search(
        r'data-preview-target="content"[^>]*>(.*?)'
        r'</div>(?:<div[^>]*>)?<button[^>]*data-preview-target="button"',
        document,
        re.DOTALL,
    )
    return match.group(1) if match else ""


def _link_count(document: str, href: str) -> int | None:
    match = re.search(
        rf'<a[^>]*href="{href}"[^>]*>(.*?)</a>', document, re.DOTALL
    )
    if not match:
        return None
    count = re.search(r"[\d,.]+(?:[kKmM])?", _text(match.group(1)))
    return _number(count.group(0)) if count else None


def _external_links(document: str) -> list[str]:
    links = []
    for value in re.findall(r'<a[^>]*href="([^"]+)"', document):
        url = html.unescape(value).split("<", 1)[0].strip()
        parsed = urlsplit(url)
        if parsed.scheme in {"http", "https"} and parsed.hostname not in {
            "allpoetry.com",
            "www.allpoetry.com",
        }:
            links.append(url)
    return list(dict.fromkeys(links))


def _number(value: str) -> int:
    value = value.strip().replace(",", "").casefold()
    multiplier = {"k": 1_000, "m": 1_000_000}.get(value[-1], 1)
    if multiplier != 1:
        value = value[:-1]
    return int(Decimal(value) * multiplier)


def _text(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())
