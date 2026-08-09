from user_scanner.core.cross_scan import (
    CrossScanConfig,
    _already_swept,
    _followable,
    _fresh_pivots,
    _named_targets,
    _scope,
)
from user_scanner.core.helpers import ScanConfig
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
