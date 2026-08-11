import html
import re

from user_scanner.core.orchestrator import generic_validate, Result

# The profile header block, from the avatar to the close of its section. Only
# this span belongs to the user: the page footer carries IFTTT's own corporate
# accounts (twitter.com/IFTTT, facebook.com/ifttt, instagram.com/iftttapp),
# which a document-wide sweep would report as the user's.
_BLOCK_START = '<div class="platform-avatar-container">'
_BLOCK_END = "</section>"

_AVATAR_RE = re.compile(r'<img[^>]*class="maker-avatar"[^>]*src="([^"]+)"')
_PARAGRAPH_RE = re.compile(r"<p>(.*?)</p>", re.S)
_ANCHOR_RE = re.compile(r"<a\b[^>]*>.*?</a>", re.S)
_LINK_RE = re.compile(r'<a\b[^>]*href="(https?://[^"]+)"', re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

_OWN_HOSTS = ("ifttt.com", "ift.tt")


def validate_ifttt(user: str) -> Result:
    if "." in user:
        return Result.available("Username cannot contain periods")

    url = f"https://ifttt.com/p/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            extra, media = _parse_profile(response.text)
            return Result.taken(extra=extra, media=media)

        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=url, headers=headers)


def _parse_profile(page: str) -> tuple[dict[str, str], dict[str, str]]:
    """Read the profile fields out of the header block.

    A connected account is one IFTTT signed the user in through, so the far side
    proved ownership. Facebook's is an app-scoped id that resolves to no public
    profile; other providers hand back a real handle.
    """
    start = page.find(_BLOCK_START)
    if start < 0:
        return {}, {}

    end = page.find(_BLOCK_END, start)
    if end < 0:
        return {}, {}

    block = page[start:end]

    bio = ""
    joined = ""
    for paragraph in _PARAGRAPH_RE.findall(block):
        text = _text_of(_ANCHOR_RE.sub(" ", paragraph))
        if not joined and text.startswith("Joined "):
            joined = text.removeprefix("Joined ")
        elif text and not bio:
            bio = text

    links = [link for link in _LINK_RE.findall(block) if not _is_own_link(link)]
    extra = {"joined": joined, "bio": bio, "connected_accounts": ", ".join(links)}

    media = {}
    avatar = _AVATAR_RE.search(block)
    if avatar:
        media["avatar"] = _absolute(avatar.group(1))

    return extra, media


def _text_of(markup: str) -> str:
    return _WHITESPACE_RE.sub(" ", html.unescape(_TAG_RE.sub(" ", markup))).strip()


def _is_own_link(link: str) -> bool:
    host = link.split("/")[2].lower().removeprefix("www.")
    return host in _OWN_HOSTS


def _absolute(src: str) -> str:
    return f"https:{src}" if src.startswith("//") else src
