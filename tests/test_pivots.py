from pathlib import Path

import pytest

from user_scanner.core.pivots import (
    _HOST_ROUTES,
    _SUBDOMAIN_ROUTES,
    Pivot,
    PivotKind,
    extract_pivots,
    is_platform_host,
    rank_usernames,
    resolve_url,
    select_pivots,
)
from user_scanner.core.result import Result

USER_SCAN_ROOT = Path(__file__).resolve().parent.parent / "user_scanner" / "user_scan"


def make_result(site_name="Gravatar", extra=None, found=True, **kwargs):
    factory = Result.taken if found else Result.available
    return factory(extra=extra or {}, **kwargs).update(site_name=site_name, is_email=True)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/johndoe", ("github", "johndoe")),
        ("https://www.linkedin.com/in/johndoe/", ("linkedin", "johndoe")),
        ("https://br.linkedin.com/in/johndoe", ("linkedin", "johndoe")),
        ("https://x.com/JohnDoe2", ("x", "JohnDoe2")),
        ("https://twitter.com/JohnDoe2", ("x", "JohnDoe2")),
        ("https://stackoverflow.com/users/12345/johndoe", ("stackoverflow", "johndoe")),
        ("https://www.youtube.com/@johndoe", ("youtube", "johndoe")),
        ("https://mastodon.social/@johndoe", ("mastodon", "johndoe")),
        ("https://johndoe.tumblr.com/", ("tumblr", "johndoe")),
        ("https://johndoe.github.io", ("github", "johndoe")),
        ("https://bsky.app/profile/johndoe.bsky.social", ("bluesky", "johndoe")),
        ("https://www.reddit.com/user/johndoe/", ("reddit", "johndoe")),
    ],
)
def test_resolve_url_reads_the_handle(url, expected):
    assert resolve_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/channel/UCMandQh49QaAH2ZfHWZdEFA",
        "https://open.spotify.com/user/21jxv335g4w6dikpyyhtlbybq",
        "https://github.com/settings/profile",
        "https://x.com/i/flow/login",
        "https://github.com/",
        "ftp://github.com/johndoe",
        "not a url",
    ],
)
def test_resolve_url_rejects_non_profiles(url):
    assert resolve_url(url) == (None, None)


def test_a_platform_with_no_portable_handle_is_still_a_platform():
    """A routed host with no path pattern yields no pivot, but must not be
    mistaken for the target's own domain."""
    assert resolve_url("https://open.spotify.com/") == (None, None)
    assert is_platform_host("open.spotify.com")


def test_resolve_url_reads_a_personal_domain_root_only():
    assert resolve_url("https://johndoe.com/") == (None, "johndoe")
    assert resolve_url("https://johndoe.com/contact") == (None, None)


def test_verified_accounts_outrank_owner_entered_links():
    result = make_result(
        extra={
            "username": "johndoe",
            "verified_accounts": "GitHub: https://github.com/johndoe (verified)",
            "links": "Mine: https://x.com/JohnDoe2",
        }
    )

    kinds = {(p.site, p.kind) for p in extract_pivots([result])}

    assert ("gravatar", PivotKind.HANDLE) in kinds
    assert ("github", PivotKind.VERIFIED) in kinds
    assert ("x", PivotKind.LINK) in kinds


def test_a_verified_suffix_marks_a_link_verified_under_any_key():
    result = make_result(extra={"links": "GitHub: https://github.com/johndoe (verified)"})

    assert extract_pivots([result])[0].kind is PivotKind.VERIFIED


def test_misses_are_not_mined():
    result = make_result(extra={"username": "johndoe"}, found=False)

    assert extract_pivots([result]) == []


def test_avatar_urls_are_not_pivots():
    result = make_result(extra={"avatar_url": "https://gravatar.com/avatar/abc123"})

    assert extract_pivots([result]) == []


def test_a_sites_own_homepage_is_not_a_username():
    result = make_result(site_name="Adobe", extra={"homepage": "https://adobe.com/"})

    assert extract_pivots([result]) == []


def test_select_pivots_filters_by_link_class():
    pivots = [
        Pivot("a", PivotKind.HANDLE, "Gravatar", "username"),
        Pivot("b", PivotKind.VERIFIED, "Gravatar", "verified_accounts"),
        Pivot("c", PivotKind.LINK, "Gravatar", "links"),
    ]

    assert [p.username for p in select_pivots(pivots, "all")] == ["a", "b", "c"]
    assert [p.username for p in select_pivots(pivots, "verified")] == ["a", "b"]
    assert [p.username for p in select_pivots(pivots, "none")] == ["a"]


def test_rank_usernames_prefers_the_best_vouched_casing():
    pivots = [
        Pivot("johndoe2", PivotKind.LINK, "Gravatar", "links"),
        Pivot("JohnDoe2", PivotKind.VERIFIED, "Gravatar", "verified_accounts"),
        Pivot("other", PivotKind.VERIFIED, "Gravatar", "verified_accounts"),
    ]

    assert rank_usernames(pivots) == ["JohnDoe2", "other"]


@pytest.mark.parametrize(
    "module", sorted({m for _, m, _ in _HOST_ROUTES} | {m for _, m in _SUBDOMAIN_ROUTES})
)
def test_every_route_names_a_live_user_scan_module(module):
    assert list(USER_SCAN_ROOT.glob(f"*/{module}.py")), f"no user_scan module named {module}"
