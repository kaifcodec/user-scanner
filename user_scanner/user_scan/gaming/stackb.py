import html
import json
import re
from urllib.parse import quote

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


JSON_LD_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>',
    re.DOTALL,
)
UNSAFE_PATH_RE = re.compile(r"[/#?\x00-\x1f\x7f]")


def _meta_content(response_text: str, attr: str, value: str) -> str | None:
    pattern = (
        rf'<meta\s+[^>]*{attr}=["\']{re.escape(value)}["\'][^>]*'
        r'content=["\']([^"\']*)["\'][^>]*>'
    )
    match = re.search(pattern, response_text, re.IGNORECASE)
    if match:
        return html.unescape(match.group(1)).strip()

    pattern = (
        r'<meta\s+[^>]*content=["\']([^"\']*)["\'][^>]*'
        rf'{attr}=["\']{re.escape(value)}["\'][^>]*>'
    )
    match = re.search(pattern, response_text, re.IGNORECASE)
    if match:
        return html.unescape(match.group(1)).strip()

    return None


def _canonical_url(response_text: str) -> str | None:
    match = re.search(
        r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)["\']',
        response_text,
        re.IGNORECASE,
    )
    if match:
        return html.unescape(match.group(1)).strip()

    return None


def _json_ld_profile(response_text: str) -> dict:
    for match in JSON_LD_RE.finditer(response_text):
        try:
            data = json.loads(html.unescape(match.group(1)))
        except json.JSONDecodeError:
            continue

        if data.get("@type") == "ProfilePage":
            entity = data.get("mainEntity")
            return entity if isinstance(entity, dict) else {}

    return {}


def _profile_extra(response_text: str, profile_url: str) -> dict:
    profile = _json_ld_profile(response_text)
    title = _meta_content(response_text, "property", "og:title") or ""
    meta_description = (
        _meta_content(response_text, "property", "og:description")
        or _meta_content(response_text, "name", "description")
    )
    description = profile.get("description") or meta_description

    display_name = profile.get("name")
    if not display_name and " (@" in title:
        display_name = title.split(" (@", 1)[0]

    rank = None
    followers = None
    if meta_description or description:
        rank_match = re.search(r"Ранг:\s*([^\.]+)", meta_description or description)
        if rank_match:
            rank = rank_match.group(1).strip()

        followers_match = re.search(r"Подписчики:\s*(\d+)", meta_description or description)
        if followers_match:
            followers = int(followers_match.group(1))

    if followers is None:
        followers_match = re.search(r"(\d+)\s*Подписчиков", response_text)
        if followers_match:
            followers = int(followers_match.group(1))

    return {
        "display_name": display_name,
        "bio": description,
        "avatar": profile.get("image") or _meta_content(response_text, "property", "og:image"),
        "followers": followers,
        "rank": rank,
        "profile_url": profile.get("url") or profile_url,
    }


def validate_stackb(user: str) -> Result:
    user = user.strip().lower()
    if user.startswith("@"):
        user = user[1:]
    profile_url = f"https://stackb.net/@{user}"
    url = f"https://stackb.net/@{quote(user, safe='')}"

    if not user:
        return Result.error("Username cannot be empty", url=url)

    if UNSAFE_PATH_RE.search(user):
        return Result.error("Username contains unsafe URL path characters", url=url)

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8",
    }

    def process(response):
        response_text = response.text

        if response.status_code == 404 and (
            "Страница не найдена" in response_text
            or re.search(r">\s*404\s*<", response_text)
        ):
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        og_type = _meta_content(response_text, "property", "og:type")
        canonical_url = _canonical_url(response_text)
        og_url = _meta_content(response_text, "property", "og:url")
        profile = _json_ld_profile(response_text)

        profile_urls = {canonical_url, og_url, profile.get("url")}
        has_profile_url = url in profile_urls or profile_url in profile_urls
        has_profile_identifier = profile.get("identifier") == f"@{user}"
        has_profile_component = 'name&quot;:&quot;profile&quot;' in response_text

        if (
            og_type == "profile"
            and has_profile_url
            and (has_profile_identifier or has_profile_component)
        ):
            return Result.taken(extra=_profile_extra(response_text, profile_url))

        return Result.error("Unexpected response body")

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=url,
        follow_redirects=True,
    )
