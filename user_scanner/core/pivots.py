"""Turns finished scan metadata into new scan targets.

A pivot is a target a scan implied but never tested: a handle a site reports
for the scanned email, one embedded in a link that profile carries, or an email
address the profile publishes. Nothing here makes a request — callers decide
which pivots are worth one.

Links are classified by how much the source platform vouches for them.
A *verified* link required the owner to prove control of the far side (OAuth
connection, rel="me" round-trip); a plain *link* is free text the owner typed.
Email addresses carry the same distinction: one the site published in its own
email field against one scraped out of prose the owner wrote.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Iterator, List, Optional, Tuple
from urllib.parse import unquote, urlsplit

from user_scanner.core.helpers import EMAIL_RE, is_valid_email
from user_scanner.core.result import Result

# Extra keys whose value is the account's own handle on the reporting site.
HANDLE_KEYS = frozenset(
    {
        "username",
        "user_name",
        "handle",
        "screen_name",
        "nickname",
        "login",
        "login_name",
        "preferred_username",
        "profile_name",
        "vanity",
    }
)

# Extra keys whose links the platform itself verified.
VERIFIED_KEYS = frozenset({"verified_accounts", "verified_links", "connected_accounts"})

# Extra keys named after another platform, holding a bare handle rather than a
# URL. Kick, GitHub, Unsplash, Coderwall and 500px all publish socials this way,
# and a bare handle never reaches ``_pivots_from_links``, which only matches URLs.
#
# ``discord`` is deliberately absent: sites store a server invite code there
# (Kick's ``nAZEkUNWPt``), which is not an account name.
PLATFORM_HANDLE_KEYS = {
    "bluesky": "bluesky",
    "facebook": "facebook",
    "github": "github",
    "instagram": "instagram",
    "linkedin": "linkedin",
    "mastodon": "mastodon",
    "pinterest": "pinterest",
    "reddit": "reddit",
    "soundcloud": "soundcloud",
    "spotify": "spotify",
    "tiktok": "tiktok",
    "tumblr": "tumblr",
    "twitch": "twitch",
    "twitter": "x",
    "x": "x",
    "youtube": "youtube",
}

# Suffixes a site may hang off a platform name (``twitter_handle``). ``_id`` is
# excluded on purpose so that identifier fields — YouTube's ``UC…`` channel id —
# are never read as handles.
_PLATFORM_KEY_SUFFIXES = ("_handle", "_username", "_user", "_name")

# Extra keys whose value is the account holder's own address. A key outside this
# set may still carry an address, but only as free text — which is what keeps
# package metadata (``author_email``, ``maintainer_email``) out of the trusted
# tier, since those name whoever published a release rather than the account.
EMAIL_KEYS = frozenset(
    {
        "email",
        "emails",
        "business_email",
        "contact_email",
        "public_email",
        "paypal_email",
        "verified_email",
    }
)

# Local parts that address a role or a robot rather than a person. Kept to the
# RFC 2142 mandated names and the no-reply family: a freelancer really does take
# mail at ``hello@`` or ``contact@``, so those stay in.
_ROLE_LOCAL_PARTS = frozenset(
    {
        "abuse",
        "do-not-reply",
        "donotreply",
        "hostmaster",
        "mailer-daemon",
        "no-reply",
        "noreply",
        "postmaster",
        "webmaster",
    }
)

# Domains that hold no mailbox: RFC 2606 documentation placeholders, the
# stand-ins people type into a bio, and the relay GitHub substitutes when an
# account hides its address.
_NON_MAILBOX_DOMAINS = frozenset(
    {
        "domain.com",
        "email.com",
        "example.com",
        "example.net",
        "example.org",
        "users.noreply.github.com",
        "yourdomain.com",
    }
)

_NON_MAILBOX_TLDS = (".example", ".invalid", ".localhost", ".test")

# Substrings marking a value as an image URL — never a pivot.
_MEDIA_KEY_PARTS = (
    "avatar",
    "image",
    "photo",
    "picture",
    "thumbnail",
    "icon",
    "banner",
    "background",
    "snapcode",
    "pfp",
    "logo",
)

_URL_RE = re.compile(r"https?://[^\s,;\"'<>()\[\]]+", re.I)
_VERIFIED_SUFFIX_RE = re.compile(r"\s*\(verified\)", re.I)
_HANDLE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~-]{1,63}$")

# Path segments and domain labels that name a site's own pages rather than a
# person, so a bare-segment route must never hand them back as a handle.
_RESERVED = frozenset(
    {
        "about", "account", "accounts", "admin", "all", "api", "assets", "auth",
        "best", "blog", "categories", "category", "channel", "channels", "contact",
        "cookies", "dashboard", "developer", "developers", "discover", "docs",
        "download", "downloads", "embed", "en", "event", "events", "explore",
        "faq", "feed", "feeds", "features", "forum", "forums", "group", "groups",
        "help", "home", "i", "images", "img", "inbox", "index", "intent", "jobs",
        "join", "learn", "legal", "login", "logout", "mail", "media", "messages",
        "new", "news", "notifications", "oauth", "p", "page", "pages", "playlist",
        "popular", "press", "pricing", "privacy", "products", "profile", "public",
        "register", "results", "rss", "search", "secure",
        "settings", "share", "shop", "signin", "signup", "sitemap", "static",
        "store", "support", "tag", "tags", "terms", "top", "topic", "topics",
        "tos", "trending", "us", "user", "users", "video", "videos", "watch",
        "web", "www",
    }
)

_BARE = r"^/(?P<user>[^/?#]+)/?$"
_AT = r"^/@(?P<user>[^/?#]+)/?$"

# host(s) -> user_scan module, path patterns yielding the handle. Every module
# named here must exist under user_scan/.
_HOST_ROUTES: Tuple[Tuple[Tuple[str, ...], str, Tuple[str, ...]], ...] = (
    (("x.com", "twitter.com"), "x", (_BARE,)),
    (("linkedin.com",), "linkedin", (r"^/in/(?P<user>[^/?#]+)/?$",)),
    (("github.com",), "github", (_BARE,)),
    (("gist.github.com",), "githubgist", (_BARE,)),
    (("gitlab.com",), "gitlab", (_BARE,)),
    (("bitbucket.org",), "bitbucket", (_BARE,)),
    (("codeberg.org",), "codeberg", (_BARE,)),
    (("gitee.com",), "gitee", (_BARE,)),
    (("stackoverflow.com",), "stackoverflow", (r"^/users/\d+/(?P<user>[^/?#]+)/?$",)),
    (
        ("youtube.com", "youtu.be"),
        "youtube",
        (_AT, r"^/c/(?P<user>[^/?#]+)/?$", r"^/user/(?P<user>[^/?#]+)/?$"),
    ),
    (("instagram.com",), "instagram", (_BARE,)),
    (("facebook.com", "fb.com"), "facebook", (_BARE,)),
    (("threads.net", "threads.com"), "threads", (_AT,)),
    (("tiktok.com",), "tiktok", (_AT,)),
    (("reddit.com",), "reddit", (r"^/u(?:ser)?/(?P<user>[^/?#]+)/?$",)),
    (("mastodon.social",), "mastodon", (_AT,)),
    (("bsky.app",), "bluesky", (r"^/profile/(?P<user>[^/?#]+)/?$",)),
    (("t.me", "telegram.me"), "telegram", (_BARE,)),
    (("twitch.tv",), "twitch", (_BARE,)),
    (("keybase.io",), "keybase", (_BARE,)),
    (("vk.com",), "vk", (_BARE,)),
    (("pinterest.com",), "pinterest", (_BARE,)),
    (("tumblr.com",), "tumblr", (_BARE,)),
    (("medium.com",), "medium", (_AT,)),
    (("dev.to",), "devto", (_BARE,)),
    (("hashnode.com",), "hashnode", (_AT,)),
    (("substack.com",), "substack", (_AT,)),
    (("about.me",), "about_me", (_BARE,)),
    (("linktr.ee",), "linktree", (_BARE,)),
    (("gravatar.com",), "gravatar", (_BARE,)),
    (("behance.net",), "behance", (_BARE,)),
    (("dribbble.com",), "dribbble", (_BARE,)),
    (("deviantart.com",), "deviantart", (_BARE,)),
    (("unsplash.com",), "unsplash", (_AT,)),
    (("flickr.com",), "flickr", (r"^/(?:photos|people)/(?P<user>[^/?#]+)/?$",)),
    (("vimeo.com",), "vimeo", (_BARE,)),
    (("dailymotion.com",), "dailymotion", (_BARE,)),
    (("soundcloud.com",), "soundcloud", (_BARE,)),
    (("mixcloud.com",), "mixcloud", (_BARE,)),
    (("last.fm",), "lastfm", (r"^/user/(?P<user>[^/?#]+)/?$",)),
    # Listed with no path pattern on purpose: /user/ carries a base62 id Spotify
    # assigns, which is portable nowhere and is not what the spotify module looks
    # up anyway (it queries stats.fm handles). Keeping the host routed still marks
    # it as a platform rather than someone's personal domain.
    (("open.spotify.com",), "spotify", ()),
    (("bandlab.com",), "bandlab", (_BARE,)),
    (("discogs.com",), "discogs", (r"^/user/(?P<user>[^/?#]+)/?$",)),
    (("npmjs.com",), "npmjs", (r"^/~(?P<user>[^/?#]+)/?$",)),
    (("pypi.org",), "pypi", (r"^/user/(?P<user>[^/?#]+)/?$",)),
    (("crates.io",), "cratesio", (r"^/users/(?P<user>[^/?#]+)/?$",)),
    (("rubygems.org",), "rubygems", (r"^/profiles/(?P<user>[^/?#]+)/?$",)),
    (("hub.docker.com",), "dockerhub", (r"^/u/(?P<user>[^/?#]+)/?$",)),
    (("huggingface.co",), "huggingface", (_BARE,)),
    (("kaggle.com",), "kaggle", (_BARE,)),
    (("hackerrank.com",), "hackerrank", (r"^/(?:profile/)?(?P<user>[^/?#]+)/?$",)),
    (("hackerone.com",), "hackerone", (_BARE,)),
    (("leetcode.com",), "leetcode", (r"^/u/(?P<user>[^/?#]+)/?$",)),
    (("codeforces.com",), "codeforces", (r"^/profile/(?P<user>[^/?#]+)/?$",)),
    (("codewars.com",), "codewars", (r"^/users/(?P<user>[^/?#]+)/?$",)),
    (("scratch.mit.edu",), "scratch", (r"^/users/(?P<user>[^/?#]+)/?$",)),
    (("figma.com",), "figma", (_AT,)),
    (("producthunt.com",), "producthunt", (_AT,)),
    (("patreon.com",), "patreon", (_BARE,)),
    (("ko-fi.com",), "kofi", (_BARE,)),
    (("buymeacoffee.com",), "buymeacoffee", (_BARE,)),
    (("liberapay.com",), "liberapay", (_BARE,)),
    (("goodreads.com",), "goodreads", (r"^/user/show/\d+-(?P<user>[^/?#]+)/?$",)),
    (("myanimelist.net",), "myanimelist", (r"^/profile/(?P<user>[^/?#]+)/?$",)),
    (("anilist.co",), "anilist", (r"^/user/(?P<user>[^/?#]+)/?$",)),
    (("chess.com",), "chess_com", (r"^/member/(?P<user>[^/?#]+)/?$",)),
    (("lichess.org",), "lichess", (r"^/@/(?P<user>[^/?#]+)/?$",)),
    (("steamcommunity.com",), "steam", (r"^/id/(?P<user>[^/?#]+)/?$",)),
    (("speedrun.com",), "speedrun", (r"^/(?:user/)?(?P<user>[^/?#]+)/?$",)),
    (("osu.ppy.sh",), "osu", (r"^/users/(?P<user>[^/?#]+)/?$",)),
    (("trello.com",), "trello", (r"^/u/(?P<user>[^/?#]+)/?$",)),
    (("imgur.com",), "imgur", (r"^/user/(?P<user>[^/?#]+)/?$",)),
    (("giphy.com",), "giphy", (r"^/channel/(?P<user>[^/?#]+)/?$",)),
    (("speakerdeck.com",), "speakerdeck", (_BARE,)),
    (("issuu.com",), "issuu", (_BARE,)),
    (("fiverr.com",), "fiverr", (_BARE,)),
    (("calendly.com",), "calendly", (_BARE,)),
    (("tradingview.com",), "tradingview", (r"^/u/(?P<user>[^/?#]+)/?$",)),
    (("openstreetmap.org",), "openstreetmap", (r"^/user/(?P<user>[^/?#]+)/?$",)),
    (("tripadvisor.com",), "tripadvisor", (r"^/Profile/(?P<user>[^/?#]+)/?$",)),
    (("duolingo.com",), "duolingo", (r"^/profile/(?P<user>[^/?#]+)/?$",)),
)

# <user>.host -> user_scan module.
_SUBDOMAIN_ROUTES: Tuple[Tuple[str, str], ...] = (
    ("tumblr.com", "tumblr"),
    ("wordpress.com", "wordpress"),
    ("blogspot.com", "blogger"),
    ("medium.com", "medium"),
    ("substack.com", "substack"),
    ("bandcamp.com", "bandcamp"),
    ("itch.io", "itch_io"),
    ("carrd.co", "carrd"),
    ("github.io", "github"),
    ("hashnode.dev", "hashnode"),
    ("gitbook.io", "gitbook"),
    ("weebly.com", "weebly"),
    ("wixsite.com", "wix"),
    ("deviantart.com", "deviantart"),
)

_ROUTES = {
    host: (module, tuple(re.compile(p) for p in patterns))
    for hosts, module, patterns in _HOST_ROUTES
    for host in hosts
}


class PivotKind(Enum):
    """How strongly the reporting platform vouches for a pivot."""

    HANDLE = "handle"
    VERIFIED = "verified"
    LINK = "link"

    @property
    def rank(self) -> int:
        return _KIND_RANK[self]


_KIND_RANK = {PivotKind.HANDLE: 0, PivotKind.VERIFIED: 1, PivotKind.LINK: 2}


@dataclass(frozen=True)
class Pivot:
    """A username worth scanning, and where it came from."""

    username: str
    kind: PivotKind
    source_site: str
    source_key: str
    site: Optional[str] = None
    url: str = ""

    @property
    def origin(self) -> str:
        return f"{self.source_site} ({self.source_key})"


class EmailKind(Enum):
    """How the source platform presented an address.

    ``FIELD`` is the site's own email field for the account; ``TEXT`` is an
    address read out of prose, where nothing says whose mailbox it is.
    """

    FIELD = "field"
    TEXT = "text"

    @property
    def rank(self) -> int:
        return 0 if self is EmailKind.FIELD else 1


@dataclass(frozen=True)
class EmailPivot:
    """An address worth scanning, and where it came from."""

    email: str
    kind: EmailKind
    source_site: str
    source_key: str

    @property
    def origin(self) -> str:
        return f"{self.source_site} ({self.source_key})"


def extract_pivots(results: Iterable[Result]) -> List[Pivot]:
    """Collect every username a set of finished results implies.

    Only results that found an account are mined — a miss carries no metadata
    worth following.
    """
    pivots: List[Pivot] = []
    seen = set()

    for result in results:
        if not result.is_found():
            continue
        for pivot in _pivots_from_result(result):
            key = (pivot.username.lower(), pivot.site, pivot.kind)
            if key in seen:
                continue
            seen.add(key)
            pivots.append(pivot)

    return sorted(pivots, key=lambda p: (p.kind.rank, p.source_site, p.username.lower()))


def select_pivots(pivots: Iterable[Pivot], links: str = "all") -> List[Pivot]:
    """Filter pivots by link class.

    ``all`` keeps everything, ``verified`` drops owner-entered links, ``none``
    keeps only handles the source site reported itself.
    """
    if links == "verified":
        return [p for p in pivots if p.kind is not PivotKind.LINK]
    if links == "none":
        return [p for p in pivots if p.kind is PivotKind.HANDLE]
    return list(pivots)


def extract_email_pivots(results: Iterable[Result]) -> List[EmailPivot]:
    """Collect every address a set of finished results exposes.

    One pivot per address *per source site*, so a caller can tell an address two
    profiles agree on from one only a single profile mentions.
    """
    pivots: List[EmailPivot] = []
    seen = set()

    for result in results:
        if not result.is_found():
            continue
        for pivot in _email_pivots_from_result(result):
            key = (pivot.email, pivot.source_site, pivot.kind)
            if key in seen:
                continue
            seen.add(key)
            pivots.append(pivot)

    return sorted(pivots, key=lambda p: (p.kind.rank, p.source_site, p.email))


def select_email_pivots(pivots: Iterable[EmailPivot], emails: str = "verified") -> List[EmailPivot]:
    """Filter address pivots by how the source presented them.

    ``all`` keeps addresses scraped from prose too, ``verified`` keeps only the
    ones a site published in its own email field, and ``none`` keeps nothing —
    unlike its ``--cross-links`` namesake, which still yields handle pivots
    because a handle is not a link. Every tier here is an address.
    """
    if emails == "none":
        return []
    if emails == "all":
        return list(pivots)
    return [pivot for pivot in pivots if pivot.kind is EmailKind.FIELD]


def rank_usernames(pivots: Iterable[Pivot]) -> List[str]:
    """Order distinct usernames by how well vouched they are, then by how many
    pivots mention them."""
    best: dict = {}

    for pivot in pivots:
        key = pivot.username.lower()
        entry = best.get(key)
        if entry is None:
            best[key] = {"username": pivot.username, "rank": pivot.kind.rank, "count": 1}
            continue
        entry["count"] += 1
        if pivot.kind.rank < entry["rank"]:
            entry["rank"] = pivot.kind.rank
            entry["username"] = pivot.username

    return [
        entry["username"]
        for entry in sorted(
            best.values(), key=lambda e: (e["rank"], -e["count"], e["username"].lower())
        )
    ]


def resolve_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Map a profile URL to ``(user_scan module, username)``.

    Returns ``(None, username)`` for a personal domain, whose handle is worth
    scanning everywhere but points at no particular site, and ``(None, None)``
    when nothing usable can be read out.
    """
    try:
        parts = urlsplit(url)
    except ValueError:
        return None, None

    if parts.scheme not in ("http", "https") or not parts.netloc:
        return None, None

    host = parts.hostname or ""
    path = unquote(parts.path or "")

    subdomain = _match_subdomain(host)
    if subdomain:
        return subdomain

    for candidate in _host_candidates(host):
        route = _ROUTES.get(candidate)
        if not route:
            continue
        module, patterns = route
        for pattern in patterns:
            match = pattern.match(path)
            if match:
                user = _clean_handle(match.group("user"), module)
                if user:
                    return module, user
        # A routed host whose path fits no profile shape is one of that site's
        # own pages, so the domain fallback must not fire for it.
        return None, None

    return None, _domain_handle(host, path)


def is_platform_host(host: str) -> bool:
    """True when a host belongs to a site the route table knows.

    Lets callers tell a personal domain from a platform without caring whether
    any particular URL on it happens to name a profile.
    """
    host = (host or "").strip().lower().rstrip(".").removeprefix("www.")
    if not host:
        return False
    if any(host == suffix or host.endswith("." + suffix) for suffix, _ in _SUBDOMAIN_ROUTES):
        return True
    return any(candidate in _ROUTES for candidate in _host_candidates(host))


def _pivots_from_result(result: Result) -> Iterator[Pivot]:
    source_site = result.site_name or "Unknown"
    own_module = module_stem(source_site)

    for key, value in result.extra.items():
        if not isinstance(value, str) or is_media_key(key):
            continue

        if key in HANDLE_KEYS:
            handle = _clean_handle(value, own_module)
            if handle:
                yield Pivot(handle, PivotKind.HANDLE, source_site, key, own_module)
            continue

        module = _platform_key_module(key)
        if module and not _URL_RE.search(value):
            handle = _clean_handle(value, module)
            if handle:
                yield Pivot(handle, PivotKind.LINK, source_site, key, module)
            continue

        yield from _pivots_from_links(value, key, source_site, own_module)


def _platform_key_module(key: str) -> Optional[str]:
    """The module a platform-named key points at — ``twitter_handle`` -> ``x``.

    Only the key names the platform; the value is the handle. Returns ``None``
    for any key that does not name a platform, so an unknown key still falls
    through to URL extraction.
    """
    name = key.lower()
    for suffix in _PLATFORM_KEY_SUFFIXES:
        name = name.removesuffix(suffix)
    return PLATFORM_HANDLE_KEYS.get(name)


def _email_pivots_from_result(result: Result) -> Iterator[EmailPivot]:
    source_site = result.site_name or "Unknown"

    for key, value in result.extra.items():
        if not isinstance(value, str) or is_media_key(key):
            continue
        kind = EmailKind.FIELD if key in EMAIL_KEYS else EmailKind.TEXT
        for candidate in _addresses_in(value):
            address = _clean_email(candidate)
            if address:
                yield EmailPivot(address, kind, source_site, key)


def _addresses_in(text: str) -> Iterator[str]:
    """Addresses in a value, minus the two shapes that only look like one.

    URLs are blanked first, because a profile link parses as a perfectly legal
    address whose local part is the host and path — ``tiktok.com/@jane.doe``
    yields ``//www.tiktok.com/@jane.doe``. Nothing is lost: links already
    reach the scan as username pivots.

    A match the text prefixes with a second ``@`` is a fediverse handle
    (``@johndoe@mastodon.social``), which is an account name, not a mailbox.
    """
    masked = _URL_RE.sub(lambda m: " " * len(m.group(0)), text)
    for match in EMAIL_RE.finditer(masked):
        if match.start() and masked[match.start() - 1] == "@":
            continue
        yield match.group(0)


def _clean_email(value: str) -> Optional[str]:
    address = value.strip().strip(".,;:").lower()
    if not is_valid_email(address):
        return None

    local, _, domain = address.rpartition("@")
    if local in _ROLE_LOCAL_PARTS or domain in _NON_MAILBOX_DOMAINS:
        return None
    if domain.startswith("noreply.") or ".noreply." in domain:
        return None
    if domain.endswith(_NON_MAILBOX_TLDS):
        return None
    return address


def _pivots_from_links(
    value: str, key: str, source_site: str, own_module: Optional[str]
) -> Iterator[Pivot]:
    for match in _URL_RE.finditer(value):
        url = match.group(0).rstrip(".,;:")
        verified = key in VERIFIED_KEYS or bool(_VERIFIED_SUFFIX_RE.match(value, match.end()))
        module, username = resolve_url(url)
        if not username:
            continue
        # A site's own address inside its own metadata names the site, not a person.
        if module is None and own_module and username.lower() == own_module:
            continue
        kind = PivotKind.VERIFIED if verified else PivotKind.LINK
        yield Pivot(username, kind, source_site, key, module, url)


def _match_subdomain(host: str) -> Optional[Tuple[str, str]]:
    for suffix, module in _SUBDOMAIN_ROUTES:
        if not host.endswith("." + suffix):
            continue
        label = host[: -len(suffix) - 1]
        if "." in label:
            continue
        user = _clean_handle(label, module)
        if user:
            return module, user
    return None


def _host_candidates(host: str) -> Iterator[str]:
    """Yield the host and each parent domain, so country and www prefixes
    (``br.linkedin.com``) reach the same route as the bare domain."""
    labels = host.split(".")
    for index in range(len(labels) - 1):
        yield ".".join(labels[index:])


def _domain_handle(host: str, path: str) -> Optional[str]:
    """Read a handle off a personal domain — only from its root page, where the
    domain label is the whole claim being made."""
    if path not in ("", "/"):
        return None
    labels = host.split(".")
    if len(labels) < 2:
        return None
    return _clean_handle(labels[-2], None)


def _clean_handle(value: str, module: Optional[str]) -> Optional[str]:
    handle = unquote(value or "").strip().strip("@").rstrip("/")
    if module == "bluesky":
        handle = handle.removesuffix(".bsky.social")
    if not _HANDLE_RE.match(handle) or handle.isdigit():
        return None
    if handle.lower() in _RESERVED:
        return None
    return handle


def module_stem(site_name: str) -> Optional[str]:
    """Reverse of ``helpers.get_site_name`` — the module file a site came from."""
    name = re.sub(r"\s*\(.*\)\s*$", "", (site_name or "").strip().lower())
    stem = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    return stem or None


def is_media_key(key: str) -> bool:
    return any(part in key for part in _MEDIA_KEY_PARTS)
