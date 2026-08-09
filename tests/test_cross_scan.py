from user_scanner.core.cross_scan import _followable, _fresh_pivots, _named_targets
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
