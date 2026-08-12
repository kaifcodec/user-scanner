"""Scores how strongly a cross-scan hit is tied to the scanned target.

A username sweep proves a handle is registered somewhere; it cannot prove the
account belongs to the person who was scanned. Common handles collide, and a
single sweep routinely turns up several unrelated people holding the same one
alongside its real owner, so a sweep hit is a lead until something ties it back.

The tie is drawn from *confirmed* hits: accounts a pivot named by site and
handle, which the target's own profile pointed at. Their names, personal
domains and profile URLs become the anchors every other hit is measured against.
"""

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple
from urllib.parse import urlsplit

from user_scanner.core.helpers import EMAIL_RE
from user_scanner.core.pivots import (
    EmailKind,
    EmailPivot,
    is_media_key,
    is_platform_host,
    module_stem,
    resolve_url,
)
from user_scanner.core.result import Result

# Extra keys naming the account holder.
NAME_KEYS = (
    "name",
    "fullname",
    "full_name",
    "display_name",
    "displayname",
    "real_name",
    "realname",
    "i_am",
)

# Bookkeeping this module writes back onto a result — never evidence about it.
_OWN_KEYS = frozenset({"confidence", "pivot_source"})

# Hosts that carry no identity — a shortener or a mailbox provider says nothing
# about who owns the profile linking to it.
_GENERIC_HOSTS = frozenset(
    {
        "amzn.to", "bit.ly", "buff.ly", "cutt.ly", "discord.gg", "docs.google.com",
        "drive.google.com", "gmail.com", "goo.gl", "google.com", "hotmail.com",
        "is.gd", "lnkd.in", "outlook.com", "ow.ly", "paypal.me", "rb.gy",
        "t.co", "tinyurl.com", "wa.me", "yahoo.com",
    }
)

_TOKEN_RE = re.compile(r"[A-Za-z]{2,}")


class Confidence(Enum):
    """How well a cross-scan hit is tied to the scanned target."""

    CONFIRMED = "confirmed"
    LIKELY = "likely"
    CANDIDATE = "candidate"
    CONFLICTING = "conflicting"

    @property
    def explanation(self) -> str:
        return _EXPLANATIONS[self]


_EXPLANATIONS = {
    Confidence.CONFIRMED: "a pivot named this exact site and handle",
    Confidence.LIKELY: "metadata matches the confirmed profiles",
    Confidence.CANDIDATE: "handle is registered; nothing ties it to the target",
    Confidence.CONFLICTING: "metadata names someone else",
}

ORDER = (
    Confidence.CONFIRMED,
    Confidence.LIKELY,
    Confidence.CANDIDATE,
    Confidence.CONFLICTING,
)


@dataclass(frozen=True)
class Anchors:
    """Identity facts a hit can be measured against."""

    names: FrozenSet[str]
    domains: FrozenSet[str]
    emails: FrozenSet[str]
    urls: FrozenSet[str]
    accounts: FrozenSet[Tuple[str, str]]
    # Domains the target was seen to *link* to, without the ones inferred from
    # harvested addresses. Judging an address by `domains` would be circular —
    # its own domain lands there the moment it is harvested.
    link_domains: FrozenSet[str]


@dataclass(frozen=True)
class RankedEmail:
    """An address a cross-scan may follow, and how well it is tied to the target."""

    email: str
    confidence: Confidence
    sources: Tuple[str, ...]
    field: bool


def build_anchors(
    confirmed: Iterable[Result],
    emails: Iterable[str] = (),
    urls: Iterable[str] = (),
) -> Anchors:
    """Collect identity facts from the accounts already tied to the target."""
    names: Set[str] = set()
    domains: Set[str] = set()
    accounts: Set[Tuple[str, str]] = set()
    email_set = {email.lower().strip() for email in emails if email}
    url_set = {_normalize_url(url) for url in urls if url}
    url_set.discard("")

    for result in confirmed:
        account = _account_of(result)
        if account:
            accounts.add(account)
        for name in _informative_names(result):
            names.add(_normalize(name))
        for text in _texts(result):
            email_set.update(match.group(0).lower() for match in EMAIL_RE.finditer(text))
            for url in _urls_in(text):
                url_set.add(_normalize_url(url))
                host = _personal_host(url)
                if host:
                    domains.add(host)
        if result.url:
            url_set.add(_normalize_url(result.url))

    email_set.discard("")
    link_domains = domains - _GENERIC_HOSTS
    domains.update(email.split("@", 1)[1] for email in email_set if "@" in email)
    domains -= _GENERIC_HOSTS

    names.discard("")
    return Anchors(
        names=frozenset(names),
        domains=frozenset(domains),
        emails=frozenset(email_set),
        urls=frozenset(url_set),
        accounts=frozenset(accounts),
        link_domains=frozenset(link_domains),
    )


def score(result: Result, anchors: Anchors, confirmed: bool = False) -> Confidence:
    """Rate one hit against the anchors."""
    if confirmed:
        return Confidence.CONFIRMED

    names = _informative_names(result)

    if any(_normalize(name) in anchors.names for name in names):
        return Confidence.LIKELY

    if _links_a_confirmed_account(result, anchors):
        return Confidence.LIKELY

    if _echoes_anchor(result, anchors):
        return Confidence.LIKELY

    if anchors.names and any(_is_person_name(name) for name in names):
        return Confidence.CONFLICTING

    return Confidence.CANDIDATE


def rank_emails(pivots: Iterable[EmailPivot], anchors: Anchors) -> List[RankedEmail]:
    """Rate every extracted address, best-tied first.

    One handle can belong to several people, so the addresses their profiles
    carry are not equally likely to be the target's. Two independent sites
    publishing the same address in their own email field is the strongest signal
    available without sending mail, so it outranks a single site saying it once.

    ``CONFLICTING`` is never returned: an address carries no name to disagree
    with, and inventing a mismatch from the local part would mislabel every
    shared mailbox.
    """
    by_email: Dict[str, List[EmailPivot]] = {}
    for pivot in pivots:
        by_email.setdefault(pivot.email, []).append(pivot)

    ranked = [
        RankedEmail(
            email=email,
            confidence=_rate_email(email, group, anchors),
            sources=tuple(sorted({pivot.origin for pivot in group})),
            field=any(pivot.kind is EmailKind.FIELD for pivot in group),
        )
        for email, group in by_email.items()
    ]
    return sorted(ranked, key=lambda r: (ORDER.index(r.confidence), -len(r.sources), r.email))


def _rate_email(email: str, group: List[EmailPivot], anchors: Anchors) -> Confidence:
    # Deliberately not consulting anchors.emails: build_anchors harvests
    # addresses out of the very profiles being ranked here, so matching against
    # it would promote every address on a confirmed profile to CONFIRMED on the
    # strength of its own appearance.
    fields = {pivot.source_site for pivot in group if pivot.kind is EmailKind.FIELD}
    if len(fields) >= 2:
        return Confidence.CONFIRMED
    if fields:
        return Confidence.LIKELY

    # link_domains, not domains: the latter absorbs the domain of every address
    # harvested from these same profiles, which would rate each one LIKELY on
    # the strength of its own appearance.
    if email.rpartition("@")[2] in anchors.link_domains:
        return Confidence.LIKELY

    return Confidence.CANDIDATE


def _links_a_confirmed_account(result: Result, anchors: Anchors) -> bool:
    """True when the profile points at an account already tied to the target.

    Matching is on the resolved (site, handle) pair rather than on the URL text,
    so an old host or a different casing still lands — a profile linking
    ``twitter.com/JohnDoe2`` names the same account as a confirmed
    ``x.com/JohnDoe2``.
    """
    own = _account_of(result)
    for text in _texts(result):
        for url in _urls_in(text):
            site, handle = resolve_url(url)
            if not site or not handle:
                continue
            account = (site, handle.lower())
            if account != own and account in anchors.accounts:
                return True
    return False


def _echoes_anchor(result: Result, anchors: Anchors) -> bool:
    haystack = " ".join(_texts(result)).lower()
    if not haystack:
        return False
    if any(email in haystack for email in anchors.emails):
        return True
    stripped = _strip_schemes(haystack)
    if any(url and url in stripped for url in anchors.urls):
        return True
    return any(domain in stripped for domain in anchors.domains)


def _account_of(result: Result) -> Optional[Tuple[str, str]]:
    stem = module_stem(str(result.site_name or ""))
    username = str(result.username or "").lower()
    return (stem, username) if stem and username else None


def _is_person_name(value: str) -> bool:
    """True when a value reads as somebody's name rather than a label.

    Two or more word-like tokens is the bar: ``Other Person`` names a person,
    ``john.d.oe`` is a rendering of the handle.
    """
    return len(_TOKEN_RE.findall(value)) >= 2


def _informative_names(result: Result) -> List[str]:
    """The names on a result that say more than its own handle already does.

    A profile whose display name just restates the handle it was found under
    (``johndoe`` → ``john.d.oe``) is echoing the search, not naming anybody. The
    comparison is against *this* account's handle: another account's handle may
    legitimately be the person's full name, and must not silence it here.
    """
    own = _normalize(str(result.username or ""))
    return [name for name in _names(result) if _normalize(name) and _normalize(name) != own]


def _names(result: Result) -> List[str]:
    """The name each name-bearing field claims.

    Some sites pack a descriptor into the field, rendering it as
    ``Other Person, 44, male`` — so only the leading segment is the
    name, and reading the whole string would call every such profile a mismatch.
    """
    return [
        str(result.extra[key]).split(",", 1)[0].strip()
        for key in NAME_KEYS
        if result.extra.get(key)
    ]


def _texts(result: Result) -> List[str]:
    """Every value that could carry a link or an address.

    Sites name these fields as they please — ``bio``, ``website``,
    ``showcased_links``, or one key per platform — so anything that is not an
    image or this module's own bookkeeping is read.
    """
    texts = [
        str(value)
        for key, value in result.extra.items()
        if key not in _OWN_KEYS and not is_media_key(key) and isinstance(value, str)
    ]
    if result.url:
        texts.append(str(result.url))
    return texts


def _urls_in(text: str) -> List[str]:
    return re.findall(r"https?://[^\s,;\"'<>()\[\]]+", text)


def _personal_host(url: str) -> str:
    """The host of a URL that belongs to the target rather than to a platform."""
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""
    host = host.removeprefix("www.")
    if not host or host in _GENERIC_HOSTS or is_platform_host(host):
        return ""
    return host


def _normalize_url(url: str) -> str:
    return _strip_schemes(url.strip().lower()).rstrip("/")


def _strip_schemes(value: str) -> str:
    return value.replace("https://", "").replace("http://", "").replace("www.", "")


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", without_marks.lower())
