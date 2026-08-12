import pytest

from user_scanner.core.cross_scan import (
    CrossScanConfig,
    _already_scanned,
    _already_swept,
    _email_scope,
    _fresh_emails,
    _followable,
    _fresh_pivots,
    _named_targets,
    _scope,
    _split_budget,
)
from user_scanner.core.helpers import ScanConfig, get_site_name, is_loud
from user_scanner.core.pivots import PivotKind
from user_scanner.core.result import Result


def source(**extra):
    return [Result.taken(extra=extra).update(site_name="Gravatar", is_email=True)]


GRAVATAR = source(username="johndoe", links="https://github.com/johndoe")


def test_fresh_pivots_returns_everything_on_the_first_round():
    pivots = _fresh_pivots(GRAVATAR, "all", swept=set(), checked=set())

    assert {(p.site, p.username) for p in pivots} == {("gravatar", "johndoe"), ("github", "johndoe")}


def test_a_swept_username_is_never_revisited():
    pivots = _fresh_pivots(GRAVATAR, "all", swept={"johndoe"}, checked=set())

    assert pivots == []


def test_a_checked_pair_is_not_rechecked():
    pivots = _fresh_pivots(GRAVATAR, "all", swept=set(), checked={("github", "johndoe")})

    assert {p.site for p in pivots} == {"gravatar"}


def test_a_siteless_pivot_survives_until_its_username_is_swept():
    pivots = _fresh_pivots(source(bio="https://johndoe.com/"), "all", set(), {("x", "johndoe")})

    assert [(p.site, p.username, p.kind) for p in pivots] == [(None, "johndoe", PivotKind.LINK)]


def test_only_non_conflicting_hits_are_followed():
    hits = [
        Result.taken(extra={"confidence": "confirmed"}).update(site_name="Github"),
        Result.taken(extra={"confidence": "candidate"}).update(site_name="Roblox"),
        Result.taken(extra={"confidence": "conflicting"}).update(site_name="Chess.com"),
        Result.available().update(site_name="Steam"),
    ]

    assert [r.site_name for r in _followable(hits)] == ["Github", "Roblox"]


def test_the_same_account_linked_twice_is_checked_once():
    """Two profiles linking one account — in any casing — is one request."""
    pivots = _fresh_pivots(
        [
            Result.taken(extra={"verified_accounts": "X: https://x.com/JohnDoe2 (verified)"})
            .update(site_name="Gravatar", is_email=True),
            Result.taken(extra={"links": "https://twitter.com/johndoe2"})
            .update(site_name="Linktree", is_email=True),
        ],
        "all",
        swept=set(),
        checked=set(),
    )
    targets = _named_targets(pivots, swept=set(), checked=set(), configs=ScanConfig())

    assert len(pivots) == 2
    assert [m.__name__ for mods in targets.values() for m in mods] == ["x"]
    # The best-vouched pivot supplies the casing that gets scanned.
    assert list(targets) == ["JohnDoe2"]


def test_a_username_pass_does_not_rescan_its_own_target():
    """A -u pass is already a sweep of its own handle, and sites echo that handle
    back as a pivot, so it must start out marked as swept."""
    prior = [
        Result.taken(extra={"username": "JohnDoe"}).update(site_name="Chess.com", username="JohnDoe")
    ]

    assert _already_swept(prior) == {"johndoe"}
    assert _fresh_pivots(prior, "all", _already_swept(prior), set()) == []


def test_an_email_pass_seeds_nothing():
    prior = [
        Result.taken(extra={"username": "johndoe"}).update(
            site_name="Gravatar", username="johndoe@gmail.com", is_email=True
        )
    ]

    assert _already_swept(prior) == set()
    assert [p.username for p in _fresh_pivots(prior, "all", set(), set())] == ["johndoe"]


def test_an_unrestricted_run_has_no_scope():
    assert _scope(CrossScanConfig(), ScanConfig()) is None


def test_a_module_restriction_resolves_against_user_scan():
    """-m names email modules on an email run, so the sweep must re-resolve the
    same site names against user_scan."""
    scope = _scope(CrossScanConfig(modules=("github", "chess.com")), ScanConfig())

    assert sorted(m.__name__ for m in scope) == ["chess_com", "github"]


def test_a_category_restriction_resolves_to_that_folder():
    scope = _scope(CrossScanConfig(categories=("donation",)), ScanConfig())

    assert scope and all("donation" in str(m.__file__) for m in scope)


def test_named_checks_stay_inside_the_scope():
    """A pivot naming a site outside -m/-c must not be checked either."""
    pivots = _fresh_pivots(
        source(verified_accounts="GitHub: https://github.com/johndoe (verified), "
                                 "LinkedIn: https://www.linkedin.com/in/johndoe (verified)"),
        "all",
        swept=set(),
        checked=set(),
    )
    scope = _scope(CrossScanConfig(modules=("github",)), ScanConfig())
    targets = _named_targets(pivots, set(), set(), ScanConfig(), scope)

    assert [m.__name__ for mods in targets.values() for m in mods] == ["github"]


def user_hit(site_name, **extra):
    return Result.taken(extra=extra).update(site_name=site_name, username="johndoe")


def test_an_email_pass_does_not_rescan_its_own_target():
    prior = [Result.taken().update(site_name="Spotify", username="John@Acme.dev", is_email=True)]

    assert _already_scanned(prior) == {"john@acme.dev"}
    assert _fresh_emails(prior, "all", _already_scanned(prior)) == []


def test_a_username_pass_seeds_no_scanned_address():
    assert _already_scanned([user_hit("Github", email="john@acme.dev")]) == set()


def test_verified_is_the_default_and_drops_prose_addresses():
    source = [user_hit("Github", email="john@acme.dev", bio="also loose@random.net")]

    assert [e.email for e in _fresh_emails(source, "verified", set())] == ["john@acme.dev"]
    assert len(_fresh_emails(source, "all", set())) == 2
    assert _fresh_emails(source, "none", set()) == []


@pytest.mark.parametrize(
    "budget,usernames,emails,expected",
    [
        (3, 5, 2, (2, 1)),
        (3, 0, 2, (0, 2)),   # nothing to sweep, addresses take the lot
        (3, 5, 0, (3, 0)),   # no addresses, usernames keep the pre-existing budget
        (1, 2, 2, (1, 0)),   # a budget of 1 still sweeps a username first
        (2, 1, 3, (1, 1)),
        (0, 5, 5, (0, 0)),
    ],
)
def test_neither_target_kind_starves_the_other(budget, usernames, emails, expected):
    assert _split_budget(budget, usernames, emails) == expected


def test_loud_email_modules_are_skipped_rather_than_prompted():
    """The addresses reaching a cross-scan came off somebody else's profile, so
    mailing them is not a decision this pass gets to make."""
    quiet = _email_scope(CrossScanConfig(), ScanConfig())
    loud_names = {m.__name__ for m in quiet if is_loud(get_site_name(m), is_email=True)}

    assert loud_names == set()
    assert _email_scope(CrossScanConfig(), ScanConfig(allow_loud=True)) is None


def test_a_module_restriction_resolves_against_email_scan():
    scope = _email_scope(CrossScanConfig(modules=("github",)), ScanConfig())

    assert [m.__name__ for m in scope] == ["github"]


def test_emails_none_loads_no_module_at_all():
    assert _email_scope(CrossScanConfig(emails="none"), ScanConfig()) == []
