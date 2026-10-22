import re
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

_TITLE_RE = re.compile(r"<title>([^<]*)</title>")
_NAME_RE = re.compile(r'<h2 class="marginbottom5">([^<]+)</h2>')
_AVATAR_RE = re.compile(r'src="(/img/avatars/[^"]+)"')
_ACTIVITY_RE = re.compile(r"Last activity:\s*([^<]+?)\s*</span>")
_AGE_RE = re.compile(r"Age:\s*(\d+)")
_COUNTRY_RE = re.compile(r'Country:\s*<img src="/gfx/flags/[^"]+" alt="([^"]+)"')
_MODS_RE = re.compile(r"</i>\s*([\d.,]+)\s*Mods</a>")
_DOWNLOADS_RE = re.compile(r"</i>\s*([\d.,]+)\s*Downloads")
_COMMENTS_RE = re.compile(r"</i>\s*([\d.,]+)\s*Comments")


def _count(raw: str) -> int | str:
    value = raw.replace(".", "").replace(",", "")
    return int(value) if value.isdigit() else raw


def validate_gtainside(user: str) -> Result:
    """
    Check account existence on GTAinside.com via its public profile page.

    Existing profiles return 200 with a "<name>'s profile | GTAinside.com"
    title; missing profiles return a dedicated 404 page whose title is
    "Page not found - 404". Both markers are verified explicitly so a WAF or
    challenge page can never be mistaken for a verdict.

    Sidebar stats (age, country, mods, downloads, comments) are extracted
    when present; valid profiles exist without any of them (e.g. users who
    never filled in their details or never uploaded mods).
    """
    url = f"https://www.gtainside.com/profile/{quote(user, safe='')}"
    show_url = url

    def process(response):
        text = response.text
        title_match = _TITLE_RE.search(text)
        title = title_match.group(1) if title_match else ""

        # Available state: the dedicated 404 page, identified by its own
        # title and error block — not just the bare status code.
        if response.status_code == 404 and title == "Page not found - 404":
            return Result.available(url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        # Taken state: profile pages carry a title ending in "'s profile |
        # GTAinside.com", which the 404/challenge pages never produce.
        if not title.endswith("'s profile | GTAinside.com"):
            return Result.error("Missing GTAinside profile markers")

        name_match = _NAME_RE.search(text)
        extra = {}
        if name_match:
            extra["fullname"] = name_match.group(1).strip()
        activity_match = _ACTIVITY_RE.search(text)
        if activity_match:
            extra["last_activity"] = " ".join(activity_match.group(1).split())

        # Sidebar stats — all optional: some valid profiles (e.g. users who
        # never filled in their details) omit age/country, and accounts
        # without uploads show "No mods uploaded yet." instead of counts.
        age_match = _AGE_RE.search(text)
        if age_match:
            extra["age"] = int(age_match.group(1))
        country_match = _COUNTRY_RE.search(text)
        if country_match:
            extra["country"] = country_match.group(1)
        mods_match = _MODS_RE.search(text)
        if mods_match:
            extra["mods"] = _count(mods_match.group(1))
        downloads_match = _DOWNLOADS_RE.search(text)
        if downloads_match:
            extra["downloads"] = _count(downloads_match.group(1))
        comments_match = _COMMENTS_RE.search(text)
        if comments_match:
            extra["comments"] = _count(comments_match.group(1))

        avatar_match = _AVATAR_RE.search(text)
        media = {}
        if avatar_match:
            media["avatar"] = "https://www.gtainside.com" + avatar_match.group(1)

        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
