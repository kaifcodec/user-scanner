import html
import json
import re
from urllib.parse import quote, urlsplit

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

_LD_JSON = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_ANCHOR = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_NOT_FOUND = '<meta property="og:url" content="https://direct.me/404">'


def validate_directme(user: str) -> Result:
    url = f"https://direct.me/{quote(user, safe='')}"

    def process(response):
        document = response.text
        if response.status_code == 404 and _NOT_FOUND in response.text:
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        if not _is_profile(document, user):
            return Result.error("Direct.me profile markers were missing")

        page, person = _profile(document)
        extra = {
            "name": _meta(document, "author")
            or _meta(document, "og:title").removesuffix(" on Direct.me"),
            "bio": _bio(document, person),
            "social_links": person.get("sameAs") or _social_links(document) or None,
            "verified": 'aria-label="Verified' in document or "verified as genuine by the Direct.me team." in document,
            "created_at": page.get("dateCreated"),
            "updated_at": page.get("dateModified"),
        }
        return Result.taken(extra=extra, media={"avatar": _meta(document, "og:image")})

    return generic_validate(url, process, show_url=url, follow_redirects=True)


def _is_profile(document: str, user: str) -> bool:
    parsed = urlsplit(_meta(document, "og:url"))
    handle = parsed.path.strip("/")
    if (
        parsed.hostname != "direct.me"
        or "/" in handle
        or handle.casefold() != user.casefold()
    ):
        return False

    modern = _meta(document, "profile:username").casefold() == handle.casefold()
    legacy = f'class="avatarBlockSub textPrimary">direct.me/{handle}</a>' in document
    return modern or legacy


def _profile(document: str) -> tuple[dict, dict]:
    match = _LD_JSON.search(document)
    if not match:
        return {}, {}
    try:
        graph = json.loads(match.group(1)).get("@graph", [])
    except (AttributeError, json.JSONDecodeError):
        return {}, {}
    for page in graph:
        person = page.get("mainEntity", {})
        if page.get("@type") == "ProfilePage" and person.get("@type") == "Person":
            return page, person
    return {}, {}


def _meta(document: str, name: str) -> str:
    match = re.search(
        rf'<meta[^>]*(?:name|property)="{re.escape(name)}"[^>]*content="([^"]*)"',
        document,
        re.IGNORECASE,
    )
    return html.unescape(match.group(1)).strip() if match else ""


def _bio(document: str, person: dict) -> str:
    for pattern in (
        r'<(?:div|p)\b[^>]*class="[^"]*themePageProfileHeader__bio[^"]*"[^>]*>(.*?)</(?:div|p)>',
        r'<(?:div|p)\b[^>]*class="bio"[^>]*>(.*?)</(?:div|p)>',
    ):
        match = re.search(pattern, document, re.IGNORECASE | re.DOTALL)
        if match:
            return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", match.group(1))).split())
    description = str(person.get("description") or "").strip()
    seo_marker = f"(@{person.get('identifier') or ''}) Find their ".casefold()
    if seo_marker in description.casefold() and description.endswith(" on Direct.me."):
        return ""
    return description


def _social_links(document: str) -> list[str]:
    social_links = []
    for attributes, content in _ANCHOR.findall(document):
        classes = _attribute(attributes, "class").split()
        if "socialIcon-item" not in classes and 'class="profileSocialIcon' not in content:
            continue
        href = html.unescape(_attribute(attributes, "href"))
        if urlsplit(href).scheme in {"http", "https"} and href not in social_links:
            social_links.append(href)
    return social_links


def _attribute(attributes: str, name: str) -> str:
    match = re.search(rf'\b{re.escape(name)}="([^"]*)"', attributes, re.IGNORECASE)
    return match.group(1) if match else ""
