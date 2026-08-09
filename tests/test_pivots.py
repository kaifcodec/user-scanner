from pathlib import Path

import pytest

from user_scanner.core.pivots import (
    EmailKind,
    _HOST_ROUTES,
    _SUBDOMAIN_ROUTES,
    Pivot,
    PivotKind,
    extract_email_pivots,
    extract_pivots,
    is_platform_host,
    rank_usernames,
    resolve_url,
    select_email_pivots,
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


def user_result(site_name, **extra):
    return Result.taken(extra=extra).update(site_name=site_name, username="johndoe")


def test_a_dedicated_email_field_outranks_one_scraped_from_prose():
    pivots = extract_email_pivots(
        [user_result("GitHub", email="john@acme.dev", bio="or try other@acme.dev")]
    )

    assert [(p.email, p.kind) for p in pivots] == [
        ("john@acme.dev", EmailKind.FIELD),
        ("other@acme.dev", EmailKind.TEXT),
    ]


def test_package_metadata_is_not_the_account_holders_address():
    """author_email/maintainer_email name whoever published a release, so they
    stay out of the trusted tier that --cross-emails verified keeps."""
    pivots = extract_email_pivots([user_result("PyPI", author_email="maint@pkg.org")])

    assert [p.kind for p in pivots] == [EmailKind.TEXT]
    assert select_email_pivots(pivots, "verified") == []


def test_the_same_address_from_two_sites_is_kept_once_per_site():
    """Frequency is the ranking signal, so per-site pivots must survive dedupe."""
    pivots = extract_email_pivots(
        [user_result("GitHub", email="john@acme.dev"), user_result("Gravatar", emails="john@acme.dev")]
    )

    assert [p.source_site for p in pivots] == ["GitHub", "Gravatar"]


def test_casing_is_normalised_so_one_mailbox_is_one_target():
    pivots = extract_email_pivots([user_result("GitHub", email="John.Doe@Acme.DEV")])

    assert [p.email for p in pivots] == ["john.doe@acme.dev"]


@pytest.mark.parametrize(
    "address",
    [
        "noreply@acme.dev",
        "postmaster@acme.dev",
        "12345+johndoe@users.noreply.github.com",
        "someone@example.com",
        "someone@yourdomain.com",
        "someone@acme.test",
        "not-an-address",
    ],
)
def test_addresses_that_reach_nobody_are_dropped(address):
    assert extract_email_pivots([user_result("GitHub", email=address)]) == []


def test_a_role_lookalike_that_is_a_real_mailbox_survives():
    """hello@ and contact@ are how freelancers take mail, so they stay in."""
    pivots = extract_email_pivots([user_result("GitHub", email="hello@acme.dev")])

    assert [p.email for p in pivots] == ["hello@acme.dev"]


def test_an_avatar_url_is_never_mined_for_an_address():
    assert extract_email_pivots([user_result("GitHub", avatar_url="https://x.dev/a@b.png")]) == []


def test_none_keeps_nothing_unlike_its_links_namesake():
    """--cross-links none still yields handle pivots because a handle is not a
    link; every email tier is an address, so none means none."""
    pivots = extract_email_pivots([user_result("GitHub", email="john@acme.dev")])

    assert select_email_pivots(pivots, "all")
    assert select_email_pivots(pivots, "verified")
    assert select_email_pivots(pivots, "none") == []


def test_a_profile_link_is_not_an_address():
    """tiktok.com/@jane.doe is a legal dot-atom address whose local part is
    the host and path. Links already arrive as username pivots."""
    pivots = extract_email_pivots(
        [user_result("Cam4", social_links="https://www.tiktok.com/@jane.doe")]
    )

    assert pivots == []


def test_a_fediverse_handle_is_not_a_mailbox():
    pivots = extract_email_pivots(
        [user_result("Sourceforge", social_networks="Mastodon: @johndoe@mastodon.social")]
    )

    assert pivots == []


def test_an_address_beside_a_link_still_survives():
    pivots = extract_email_pivots(
        [user_result("Reddit", bio="site https://acme.dev/@notme and mail john@acme.dev")]
    )

    assert [p.email for p in pivots] == ["john@acme.dev"]
