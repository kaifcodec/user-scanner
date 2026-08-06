import html
import json
import re

import httpx

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

# LinkedIn whitelists social-media crawler bots for link previews, bypassing the
# anti-bot 999 response that blocks regular user agents. The preview HTML carries
# a JSON-LD Person node plus OpenGraph tags, which is all the profile metadata we
# surface. Note: bulk scanning may still trigger rate limiting (999) after a few
# rapid requests — that returns Result.error, never a verdict.
HEADERS = {"User-Agent": "Twitterbot/1.0"}


def validate_linkedin(user: str) -> Result:
    url = f"https://www.linkedin.com/in/{user}"
    show_url = f"{url}/"

    def inner(response: httpx.Response) -> Result:
        status = response.status_code
        text = response.text

        # Missing handles 404 directly; existing ones serve the profile at /in/
        # or 301 to a country host (e.g. br.linkedin.com) that carries the same
        # preview markup, so following redirects enriches the vanity case too.
        if status == 404 and "Profile Not Found" in text:
            return Result.available()
        if status == 200 and 'property="og:type" content="profile"' in text:
            extra, media = _extract(text)
            return Result.taken(extra=extra, media=media)
        return Result.error(f"[{status}] Status didn't match. Report this on Github.")

    return generic_validate(
        url, inner, show_url=show_url, headers=HEADERS, follow_redirects=True
    )


def _extract(text: str) -> tuple[dict, dict]:
    person = _find_person(text)
    extra: dict = {}
    media: dict = {}

    title = _og(text, "og:title") or ""
    title_match = re.match(r"^(.*?) - (.*?) \| LinkedIn$", title)
    # Headline-less profiles fall back to "<name> - <location> | Professional
    # Profile | LinkedIn"; that segment is boilerplate, not a real headline.
    if title_match and "| Professional Profile" not in title_match.group(2):
        extra["headline"] = title_match.group(2)

    # Sparse profiles omit the JSON-LD Person node but still carry the name in
    # meta tags, so fall back to those before the og:title's name segment.
    meta_name = " ".join(p for p in (_og(text, "profile:first_name"), _og(text, "profile:last_name")) if p)
    if name := (person.get("name") or meta_name or (title_match and title_match.group(1))):
        # LinkedIn appends pronouns to the name as a trailing "(She/Her)"; the
        # slash keeps this from stripping real parentheticals like "(PhD)".
        if pronouns := re.search(r"\s*\(([A-Za-z]+(?:/[A-Za-z]+)+)\)\s*$", name):
            extra["pronouns"] = pronouns.group(1)
            name = name[: pronouns.start()].strip()
        extra["name"] = name
    if bio := _clean_html(person.get("description")):
        extra["bio"] = bio
    if badges := person.get("disambiguatingDescription"):
        extra["badges"] = badges

    address = person.get("address") or {}
    if location := (address.get("addressLocality") or address.get("addressCountry")):
        extra["location"] = location
    if country := (address.get("addressCountry") or _country_from_url(text)):
        extra["country"] = country

    if experience := _format_orgs(person.get("worksFor")):
        extra["experience"] = experience
    # alumniOf is schema.org's field for schools, but LinkedIn also files board
    # seats and other affiliations here, so this can include non-academic orgs.
    if education := _format_orgs(person.get("alumniOf")):
        extra["education"] = education

    languages = [lang.get("name", "").strip() for lang in person.get("knowsLanguage") or []]
    if languages := [lang for lang in languages if lang]:
        extra["languages"] = ", ".join(languages)

    awards = [a.strip() for a in person.get("awards") or [] if isinstance(a, str) and a.strip()]
    if awards := list(dict.fromkeys(awards)):
        extra["awards"] = "; ".join(awards)

    if articles := _find_articles(text):
        extra["articles"] = "; ".join(articles)

    if last_published := _latest_published(text):
        extra["last_posted"] = last_published

    if similar := _similar_profiles(text):
        extra["similar_profiles"] = "; ".join(similar)

    stat = person.get("interactionStatistic") or {}
    if str(stat.get("interactionType", "")).endswith("FollowAction"):
        if (followers := stat.get("userInteractionCount")) is not None:
            extra["followers"] = str(followers)

    connections = re.search(r"([\d,]+)\+? connections on LinkedIn", _og(text, "og:description") or "")
    if connections:
        extra["connections"] = connections.group(1)

    image = (person.get("image") or {}).get("contentUrl") or _og(text, "og:image")
    if image:
        media["avatar"] = image

    return extra, media


def _find_person(text: str) -> dict:
    for node in _ld_nodes(text):
        if node.get("@type") == "Person":
            return node
    return {}


def _find_articles(text: str) -> list[str]:
    articles = []
    for node in _ld_nodes(text):
        if node.get("@type") != "Article" or not (headline := node.get("headline")):
            continue
        date = (node.get("datePublished") or "")[:10]
        articles.append(f"{headline.strip()} ({date})" if date else headline.strip())
    return list(dict.fromkeys(articles))


def _latest_published(text: str) -> str | None:
    # Newest publish date across long-form Articles and Activity-feed posts
    # (DiscussionForumPosting); the ISO-8601 prefix sorts chronologically.
    dates = [
        node["datePublished"]
        for node in _ld_nodes(text)
        if node.get("@type") in ("Article", "DiscussionForumPosting") and node.get("datePublished")
    ]
    if not dates:
        return None
    return max(dates)[:10]


def _similar_profiles(text: str) -> list[str]:
    # "Other similar profiles" (the browsemap aside) is HTML-only, not JSON-LD;
    # collect the linked names, one per profile, de-duplicated by handle.
    section = re.search(r'<section[^>]*class="[^"]*browsemap[^"]*".*?</section>', text, re.S)
    if not section:
        return []
    profiles = []
    seen = set()
    for href, inner in re.findall(
        r'<a[^>]+href="https://[a-z]{2,3}\.linkedin\.com/in/([^/?"]+)[^"]*"[^>]*>(.*?)</a>',
        section.group(0), re.S,
    ):
        name = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", inner))).strip()
        if name and href not in seen:
            seen.add(href)
            profiles.append(f"{name} ({href})")
    return profiles


def _ld_nodes(text: str):
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        yield from data.get("@graph", [data])


def _format_orgs(nodes: list | None) -> str:
    formatted = []
    for org in nodes or []:
        name = (org.get("name") or "").strip()
        if not name:
            continue
        member = org.get("member") or {}
        start, end = member.get("startDate"), member.get("endDate")
        if start and end:
            formatted.append(f"{name} ({start}–{end})")
        elif start:
            formatted.append(f"{name} ({start})")
        else:
            formatted.append(name)
    return ", ".join(formatted)


def _country_from_url(text: str) -> str | None:
    # LinkedIn 301s a profile's vanity handle to its country host (e.g.
    # br.linkedin.com); US profiles stay on www, which is not a country. The host
    # code matches ISO 3166 alpha-2 except LinkedIn's "uk" (ISO "GB"), normalized
    # so this fallback stays consistent with the JSON-LD addressCountry.
    host = re.sub(r"https?://", "", _og(text, "og:url") or "").split("/")[0]
    subdomain = host.split(".")[0]
    if len(subdomain) != 2:
        return None
    return "GB" if subdomain == "uk" else subdomain.upper()


def _clean_html(value: str | None) -> str:
    # LinkedIn stores the bio as HTML, so <br> tags and entities (&gt;, &amp;)
    # leak into the JSON-LD description; turn breaks into spaces and decode them.
    if not value:
        return ""
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _og(text: str, prop: str) -> str | None:
    match = re.search(rf'<meta[^>]+property="{re.escape(prop)}"[^>]+content="([^"]*)"', text) or \
        re.search(rf'<meta[^>]+name="{re.escape(prop)}"[^>]+content="([^"]*)"', text)
    return html.unescape(match.group(1)) if match else None
