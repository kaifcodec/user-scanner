"""Second scan pass driven by the first pass's metadata.

An email scan proves an account exists but rarely names it. When a profile does
expose a handle or a link to another platform, that handle can be scanned as a
username — reaching accounts no email check can see.

Two kinds of hit come out of that, and they are not equally trustworthy: a site
a pivot named by handle, and a site where the same handle merely happens to be
taken. Every hit is scored so the difference survives into the report.
"""

from dataclasses import dataclass
from types import ModuleType
from typing import Dict, Iterable, List, Optional, Set, Tuple

from colorama import Fore, Style

from user_scanner.core.confidence import ORDER, Confidence, build_anchors, score
from user_scanner.core.helpers import ScanConfig, find_module, load_categories, load_modules
from user_scanner.core.orchestrator import run_user_full, run_user_module
from user_scanner.core.pivots import (
    Pivot,
    extract_pivots,
    module_stem,
    rank_usernames,
    select_pivots,
)
from user_scanner.core.result import Result

DEFAULT_SWEEP = 3
DEFAULT_DEPTH = 1
LINK_CHOICES = ("all", "verified", "none")

_CONFIDENCE_COLOR = {
    Confidence.CONFIRMED: Fore.GREEN,
    Confidence.LIKELY: Fore.CYAN,
    Confidence.CANDIDATE: Fore.WHITE,
    Confidence.CONFLICTING: Fore.YELLOW,
}


@dataclass(frozen=True)
class CrossScanConfig:
    links: str = "all"
    # Module and category names the run was restricted to, so -m and -c narrow
    # this pass exactly as they narrowed the first one. Names, not modules: an
    # email run's -m names email modules, and the sweep needs the username
    # module of the same site.
    modules: Tuple[str, ...] = ()
    categories: Tuple[str, ...] = ()
    # How many usernames may be swept against every module, across all rounds.
    # Zero turns sweeping off entirely, leaving only the sites a pivot named.
    sweep: int = DEFAULT_SWEEP
    depth: int = DEFAULT_DEPTH


def run_cross_scan(
    results: List[Result], configs: ScanConfig, cross_configs: CrossScanConfig
) -> List[Result]:
    """Mine finished results for usernames and scan them.

    Runs ``depth`` rounds: each round pivots off the accounts the previous one
    found, so a handle reachable only through a chain of profile links is still
    reached. Returns every round's results; the caller owns merging them into
    its own list for export.
    """
    print(f"\n{Fore.MAGENTA}== CROSS-SCAN =={Style.RESET_ALL}")

    scope = _scope(cross_configs, configs)
    if scope is not None and not scope:
        print(
            f"{Fore.YELLOW}[!] The -m/-c restriction names no username module, so "
            f"there is nothing to cross-scan.{Style.RESET_ALL}"
        )
        return []

    depth = max(1, cross_configs.depth)
    budget = max(0, cross_configs.sweep)
    all_pivots: List[Pivot] = []
    cross_results: List[Result] = []
    swept: Set[str] = _already_swept(results)
    checked: Set[Tuple[str, str]] = set()
    source: List[Result] = list(results)

    for round_number in range(1, depth + 1):
        pivots = _fresh_pivots(source, cross_configs.links, swept, checked)
        if not pivots:
            if round_number == 1:
                print(f"{Fore.YELLOW}[!] No usernames or links to pivot from.{Style.RESET_ALL}")
                return []
            print(f"\n{Fore.CYAN}[i] Round {round_number}: nothing new to follow.{Style.RESET_ALL}")
            break

        if depth > 1:
            print(f"\n{Fore.MAGENTA}-- round {round_number} of {depth} --{Style.RESET_ALL}")
        _print_pivots(pivots)
        all_pivots.extend(pivots)

        usernames = _sweep_targets(pivots, budget)
        budget -= len(usernames)
        swept.update(username.lower() for username in usernames)

        round_results: List[Result] = []
        for username in usernames:
            print(
                f"\n{Fore.CYAN}[+] Sweeping every module for username: {username}{Style.RESET_ALL}"
            )
            swept_results = (
                run_user_full(username, configs)
                if scope is None
                else run_user_module(scope, username, configs)
            )
            round_results.extend(_tag(swept_results, all_pivots, username))

        for username, modules in _named_targets(pivots, swept, checked, configs, scope).items():
            print(
                f"\n{Fore.CYAN}[+] Checking {username} on its {len(modules)} linked "
                f"site(s){Style.RESET_ALL}"
            )
            round_results.extend(
                _tag(run_user_module(modules, username, configs), all_pivots, username)
            )

        checked.update((p.site, p.username.lower()) for p in pivots if p.site)
        cross_results.extend(round_results)

        if round_number < depth:
            _apply_confidence(results, cross_results, all_pivots)
            source = _followable(round_results)

    _apply_confidence(results, cross_results, all_pivots)
    _print_summary(results, cross_results)
    return cross_results


def _scope(
    cross_configs: CrossScanConfig, configs: ScanConfig
) -> Optional[List[ModuleType]]:
    """The user_scan modules this run is allowed to touch, or None if unrestricted."""
    if cross_configs.modules:
        return [
            module
            for name in cross_configs.modules
            for module in find_module(
                name.replace(".", "_"), is_email=False, no_nsfw=configs.no_nsfw
            )
        ]
    if cross_configs.categories:
        paths = load_categories(False, configs.no_nsfw)
        return [
            module
            for name in cross_configs.categories
            if name in paths
            for module in load_modules(paths[name])
        ]
    return None


def _already_swept(results: Iterable[Result]) -> Set[str]:
    """Usernames the first pass already ran against every module.

    A username pass is itself a sweep of its own target, and sites tend to report
    that handle straight back, so without this it would rank first and spend a
    sweep repeating the scan that just finished. An email pass contributes
    nothing here — its target is not a username.
    """
    return {str(r.username).lower() for r in results if not r.is_email and r.username}


def _fresh_pivots(
    source: List[Result], links: str, swept: Set[str], checked: Set[Tuple[str, str]]
) -> List[Pivot]:
    """Pivots from ``source`` that no earlier round has already acted on.

    A swept username had every module run against it, so nothing about it is
    left to do; a named pair is done once that one site has been checked.
    """
    pivots = select_pivots(extract_pivots(source), links)
    return [
        pivot
        for pivot in pivots
        if pivot.username.lower() not in swept
        and (pivot.site is None or (pivot.site, pivot.username.lower()) not in checked)
    ]


def _followable(round_results: List[Result]) -> List[Result]:
    """The hits a further round may pivot off.

    An account whose metadata names someone else is a handle collision, and
    following its links would walk into a stranger's footprint.
    """
    return [
        result
        for result in round_results
        if result.is_found()
        and result.extra.get("confidence") != Confidence.CONFLICTING.value
    ]


def _sweep_targets(pivots: List[Pivot], budget: int) -> List[str]:
    ranked = rank_usernames(pivots)

    if budget <= 0:
        # Only a username no pivot ever tied to a site goes unchecked; one that
        # names a site elsewhere is still reached by that named check.
        routed = {p.username.lower() for p in pivots if p.site}
        unreachable = sorted({p.username for p in pivots if p.username.lower() not in routed})
        print(
            f"{Fore.YELLOW}[!] Username sweep off — checking only the sites pivots "
            f"named.{Style.RESET_ALL}"
        )
        if unreachable:
            print(
                f"{Fore.YELLOW}[!] {len(unreachable)} pivot username(s) name no site "
                f"({', '.join(unreachable)}) and are not checked{Style.RESET_ALL}"
            )
        return []

    usernames = ranked[:budget]
    deferred = ranked[len(usernames) :]
    if deferred:
        print(
            f"{Fore.YELLOW}[!] Not sweeping {len(deferred)} username(s) "
            f"({', '.join(deferred)}) — raise --cross-sweep{Style.RESET_ALL}"
        )
    return usernames


def _print_pivots(pivots: List[Pivot]) -> None:
    print(f"{Fore.GREEN}[+] {len(pivots)} pivot(s) extracted{Style.RESET_ALL}")
    for pivot in pivots:
        tag = f"[{pivot.kind.value}]"
        print(
            f"  {Fore.CYAN}{tag:<11}{Style.RESET_ALL}"
            f"{pivot.username:<24} {(pivot.site or '(any site)'):<16} "
            f"{Fore.WHITE}{pivot.origin}{Style.RESET_ALL}"
        )


def _named_targets(
    pivots: Iterable[Pivot],
    swept: Set[str],
    checked: Set[Tuple[str, str]],
    configs: ScanConfig,
    scope: Optional[List[ModuleType]] = None,
) -> Dict[str, List[ModuleType]]:
    """Modules to check for pivots whose username was not swept.

    A swept username already ran against every module, so only the pivots left
    over need their one named site checked.
    """
    # Grouped case-insensitively, matching how `swept` and `checked` compare:
    # two profiles can link the same account in different cases, and scanning it
    # once per casing is a duplicate request for one account. Pivots arrive
    # best-vouched first, so the first casing seen is the one worth reporting.
    sites_by_username: Dict[str, Set[str]] = {}
    casing: Dict[str, str] = {}
    for pivot in pivots:
        key = pivot.username.lower()
        if not pivot.site or key in swept or (pivot.site, key) in checked:
            continue
        casing.setdefault(key, pivot.username)
        sites_by_username.setdefault(key, set()).add(pivot.site)

    allowed = None if scope is None else {module.__name__ for module in scope}

    targets: Dict[str, List[ModuleType]] = {}
    for key, sites in sites_by_username.items():
        if allowed is not None:
            sites = {site for site in sites if site in allowed}
        username = casing[key]
        modules = [
            module
            for site in sorted(sites)
            for module in find_module(site, is_email=False, no_nsfw=configs.no_nsfw)
        ]
        if modules:
            targets[username] = modules
    return targets


def _tag(results: List[Result], pivots: Iterable[Pivot], username: str) -> List[Result]:
    """Record on each hit why its username was scanned.

    A username often arrives from several pivots at once; only the best-vouched
    class is reported, since that is the claim the scan rests on.
    """
    matching = [pivot for pivot in pivots if pivot.username.lower() == username.lower()]
    if not matching:
        return results

    best = min(pivot.kind.rank for pivot in matching)
    strongest = [pivot for pivot in matching if pivot.kind.rank == best]
    label = f"{strongest[0].kind.value} from {', '.join(sorted({p.origin for p in strongest}))}"

    for result in results:
        if result.is_found():
            result.update(extra={"pivot_source": label})
    return results


def _apply_confidence(
    prior: Iterable[Result], cross_results: Iterable[Result], pivots: Iterable[Pivot]
) -> None:
    """Rate every hit, and record the rating on it.

    Scoring runs once the pass is over because the anchors come from its own
    confirmed hits — a sweep hit cannot be judged before the accounts it is
    judged against have been fetched.
    """
    named = {(p.site, p.username.lower()) for p in pivots if p.site}
    hits = [r for r in cross_results if r.is_found()]
    anchors = build_anchors(
        confirmed=[r for r in hits if _is_named(r, named)],
        emails=[str(r.username) for r in prior if r.is_email and r.username],
        urls=[p.url for p in pivots if p.url],
    )

    for result in hits:
        rating = score(result, anchors, confirmed=_is_named(result, named))
        result.update(extra={"confidence": rating.value})


def _is_named(result: Result, named: Set[Tuple[str, str]]) -> bool:
    stem = module_stem(str(result.site_name or ""))
    return bool(stem) and (stem, str(result.username or "").lower()) in named


def _print_summary(prior: Iterable[Result], cross_results: Iterable[Result]) -> None:
    hits = [r for r in cross_results if r.is_found()]
    print(f"\n{Fore.CYAN}[i] Cross-scan complete.{Style.RESET_ALL}")
    print(f"  Accounts found: {len(hits)}")

    by_rating = {rating: _sites_rated(hits, rating) for rating in ORDER}
    for rating in ORDER:
        sites = by_rating[rating]
        if not sites:
            continue
        color = _CONFIDENCE_COLOR[rating]
        print(f"    {color}{rating.value:<12}{Style.RESET_ALL}{len(sites):>4}  {rating.explanation}")

    for rating in (Confidence.CONFIRMED, Confidence.LIKELY, Confidence.CONFLICTING):
        sites = by_rating[rating]
        if sites:
            color = _CONFIDENCE_COLOR[rating]
            print(f"\n  {color}{rating.value}:{Style.RESET_ALL} {', '.join(sites)}")

    prior_sites = {str(r.site_name).lower() for r in prior if r.is_found() and r.site_name}
    new_sites = sorted(
        {
            str(r.site_name)
            for r in hits
            if r.site_name and str(r.site_name).lower() not in prior_sites
        }
    )
    if not new_sites:
        print(f"\n  {Fore.YELLOW}No sites beyond the first pass.{Style.RESET_ALL}")
        return
    print(f"\n  {Fore.GREEN}New sites the first pass missed ({len(new_sites)}):{Style.RESET_ALL}")
    print(f"    {', '.join(new_sites)}")


def _sites_rated(hits: Iterable[Result], rating: Confidence) -> List[str]:
    return sorted(
        f"{r.site_name} ({r.username})"
        for r in hits
        if r.extra.get("confidence") == rating.value
    )
