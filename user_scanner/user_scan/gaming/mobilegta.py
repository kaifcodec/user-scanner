import re
from urllib.parse import quote, urljoin

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

_TITLE_RE = re.compile(r"<title>([^<]*)</title>")
_NAME_RE = re.compile(r'(?:<h1 class="userpage_user">|<h2 class="marginbottom5">)([^<]+)</h[12]>')
_AVATAR_RE = re.compile(
    r'(?:userpage_avatar"[^>]*><img\s+src="|src=")(/img/avatars/[^"]+)"'
)
_RELEASED_RE = re.compile(r"(?:Released:\s*|</i>\s*)([\d.,]+)\s*(?:mods|Mods)")
_TOTAL_DOWNLOADS_RE = re.compile(r"(?:Total:</strong>\s*|</i>\s*)([\d.,]+)\s*[dD]ownloads")
_VIEWS_RE = re.compile(r"<strong>Userpage:</strong><br>\s*(\d+)\s*Views")
_LAST_ONLINE_RE = re.compile(r"(?:<strong>Last online:</strong><br>|Last activity:\s*)<span[^>]*>([^<]+)")
_RANK_POINTS_RE = re.compile(r"I have\s+(\d+)\s+<a href=\"/en/faq.php#9\">rank points</a>")
_RANK_NAME_RE = re.compile(r"and I'm called:\s*<h2>\"?([^<\"]+)")
_COUNTRY_RE = re.compile(r'Country:\s*<img src="/gfx/flags/[^"]+"(?: alt="([^"]+)")?>\s*([^<]*)')
_AGE_RE = re.compile(r"Age:\s*(\d+)")
_CF_EMAIL_RE = re.compile(r'href="/cdn-cgi/l/email-protection#([a-f0-9]+)"')


def _count(raw: str) -> int | str:
    value = raw.replace(".", "").replace(",", "")
    return int(value) if value.isdigit() else raw


def _cf_decode(hex_bytes: str) -> str:
    """Undo Cloudflare's email-protection XOR obfuscation."""
    data = bytes.fromhex(hex_bytes)
    key = data[0]
    return "".join(chr(byte ^ key) for byte in data[1:])


def validate_mobilegta(user: str) -> Result:
    """
    Check account existence on MobileGTA.net via its public userpage.

    The site answers HTTP 200 for every /user/ URL: missing profiles carry an
    error box with "<h1>404 Not Found</h1>" and no userpage markup, while
    real profiles always render an <h1 class="userpage_user"> name plus a
    "My Stats" box. Both markers are checked explicitly — a 200 alone proves
    nothing here.

    Stats (mods released, total downloads, page views, last online, rank)
    live in the "My Stats" box and are extracted when present. Country and
    age sit in profile "block" spans, and the public contact email is a
    Cloudflare-protected link that gets decoded back to plain text — all
    three only appear when the user filled them in.
    """
    url = f"https://www.mobilegta.net/en/user/{quote(user, safe='')}"
    show_url = url

    def process(response):
        text = response.text
        title_match = _TITLE_RE.search(text)
        title = title_match.group(1) if title_match else ""

        # Available state: dedicated 404 page on GTAinside or embedded 404 block on MobileGTA
        if (
            (response.status_code == 404 and "404" in title)
            or "<h1>404 Not Found</h1>" in text
            or "Page not found" in title
        ):
            return Result.available(url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        # Taken state: the profile heading is unique to existing users.
        name_match = _NAME_RE.search(text)
        if not name_match:
            return Result.error("Missing MobileGTA/GTAinside userpage markers")

        extra: dict[str, object] = {"fullname": name_match.group(1).strip()}

        released_match = _RELEASED_RE.search(text)
        if released_match:
            extra["mods"] = int(released_match.group(1))
        downloads_match = _TOTAL_DOWNLOADS_RE.search(text)
        if downloads_match:
            extra["downloads"] = _count(downloads_match.group(1))
        views_match = _VIEWS_RE.search(text)
        if views_match:
            extra["views"] = int(views_match.group(1))
        country_match = _COUNTRY_RE.search(text)
        if country_match:
            extra["country"] = country_match.group(1).strip()
        age_match = _AGE_RE.search(text)
        if age_match:
            extra["age"] = int(age_match.group(1))
        email_match = _CF_EMAIL_RE.search(text)
        if email_match:
            # Only users who made their address public get this link; it is
            # XOR-obfuscated by Cloudflare, never stored in plain text.
            extra["email"] = _cf_decode(email_match.group(1))
        last_online_match = _LAST_ONLINE_RE.search(text)
        if last_online_match:
            last_online = " ".join(last_online_match.group(1).split())
            if last_online and last_online != "N/A":
                extra["last_online"] = last_online
        points_match = _RANK_POINTS_RE.search(text)
        if points_match:
            extra["rank_points"] = int(points_match.group(1))
        rank_name_match = _RANK_NAME_RE.search(text)
        if rank_name_match:
            extra["rank"] = rank_name_match.group(1).strip()

        avatar_match = _AVATAR_RE.search(text)
        media = {}
        # Accounts without an uploaded picture get the shared no_avatar.jpg.
        if avatar_match and not avatar_match.group(1).endswith("no_avatar.jpg"):
            avatar_src = avatar_match.group(1)
            media["avatar"] = urljoin(str(response.url), avatar_src)

        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
