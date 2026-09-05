import html
import re
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

NOT_FOUND = "The page you were looking for doesn't exist (404)"


def validate_kickstarter(user: str) -> Result:
    profile_url = f"https://www.kickstarter.com/profile/{quote(user, safe='')}"
    url = f"{profile_url}/about"

    def process(response):
        document = response.text
        if response.status_code == 404 and NOT_FOUND in document:
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")
        if (
            _meta(document, "og:type") not in {"profile", "kickstarter:creator"}
            or _meta(document, "og:url").rstrip("/").casefold()
            != profile_url.casefold()
        ):
            return Result.error("Kickstarter profile markers were missing")

        return Result.taken(
            extra={
                "name": _meta(document, "og:title"),
                "bio": _meta(document, "og:description"),
                "is_private": "This user's profile is private." in document,
                "location": _match(
                    document,
                    r'class="location[^"]*"[^>]*>\s*<a[^>]*>([^<]+)',
                ),
                "joined": _match(
                    document,
                    r'class="joined"[^>]*>.*?<time[^>]*datetime="([^"]+)"',
                ),
                "backed": _number(
                    document,
                    r'class="backed"[^>]*>\s*Backed\s+([\d,]+)\s+projects?',
                ),
                "project_count": _number(
                    document,
                    r'id="profile_created"[^>]*>.*?<span class="count">\s*([\d,]+)',
                )
                or 0,
                "badges": _badges(document),
                "websites": _websites(document),
            },
            media={"avatar": _meta(document, "og:image")},
        )

    return generic_validate(url, process, show_url=profile_url, follow_redirects=True)


def _meta(document: str, name: str) -> str:
    return _match(
        document,
        rf'<meta[^>]*property="{re.escape(name)}"[^>]*content="([^"]*)"',
    )


def _match(document: str, pattern: str) -> str:
    match = re.search(pattern, document, re.IGNORECASE | re.DOTALL)
    return html.unescape(match.group(1)).strip() if match else ""


def _number(document: str, pattern: str) -> int | None:
    value = _match(document, pattern)
    return int(value.replace(",", "")) if value else None


def _badges(document: str) -> list[str] | None:
    value = _match(document, r'data-badges="([^"]*)"')
    return re.findall(r'"([^"]+)"', value) or None


def _websites(document: str) -> list[str] | None:
    block = _match(document, r'<ul class="menu-submenu mb6">(.*?)</ul>')
    return re.findall(r'href="([^"]+)"', block) or None
