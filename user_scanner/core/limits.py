"""Bounds for the numeric scan options, shared by the CLI and the MCP server.

Every public entry point validates these values itself instead of relying on
what a downstream library happens to do with them: ``islice`` raises on a
negative stop, ``time.sleep`` on a negative delay, and a falsy timeout is
silently replaced by the default (``get_global_timeout() or 15.0``).

Each check returns the normalized value or raises ``ValueError`` with a
message that names the option, so the CLI can turn it into an argparse
usage error and the MCP server can return it to the client unchanged.
"""

import math
import sys
from typing import Any, Optional

# Longest timeout or delay accepted, in seconds. A larger value is far more
# likely a typo (milliseconds, an extra zero) than an intended hour-long wait.
MAX_SECONDS = 3600.0

# Most requests allowed in flight at once. The username orchestrator builds a
# thread pool of twice this size, so an unbounded value lets one MCP call or
# CLI typo exhaust threads or memory before any scan starts (#717). The
# defaults are 60 (username) and 25 (email).
MAX_CONCURRENCY = 500

# Rounds of link-following. Each round pivots off every account the previous
# one found, so an unbounded depth is a scan that does not finish.
MAX_CROSS_DEPTH = 5

# Full-module sweeps one cross-scan may spend. The default is 3, and each
# sweep walks every module of that target's kind.
MAX_CROSS_SWEEP = 20

# Validator calls one cross-scan may start, shared by rounds, sweeps, named
# sites, and email pivots. A username sweep is hundreds of calls, so this
# still covers the default sweep of 3 and stops a pivot graph from
# multiplying past it.
MAX_CROSS_CALLS = 4000


def check_int(name: str, value: Any, minimum: int, maximum: Optional[int] = None) -> int:
    """Return ``value`` as an int in ``[minimum, maximum]``.

    Accepts ints and integral numeric strings. Booleans and non-integral
    floats are rejected rather than truncated, so ``2.7`` never becomes 2.
    """
    if isinstance(value, bool):
        raise ValueError(f"Invalid {name} value: {value!r}")
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"Invalid {name} value: {value!r}")
        value = int(value)
    try:
        number = int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid {name} value: {value!r}") from e
    if number < minimum:
        raise ValueError(f"{name.capitalize()} must be at least {minimum}, got {number}")
    if maximum is not None and number > maximum:
        raise ValueError(f"{name.capitalize()} must be at most {maximum}, got {number}")
    return number


def check_seconds(name: str, value: Any, *, allow_zero: bool) -> float:
    """Return ``value`` as a finite number of seconds, at most ``MAX_SECONDS``.

    ``allow_zero`` separates a delay, where 0 means "no delay", from a
    timeout, where 0 would mean "fail every request immediately".
    """
    if isinstance(value, bool):
        raise ValueError(f"Invalid {name} value: {value!r}")
    try:
        seconds = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid {name} value: {value!r}") from e
    if not math.isfinite(seconds):
        raise ValueError(f"{name.capitalize()} must be a finite number of seconds, got {value!r}")
    if seconds < 0 or (seconds == 0 and not allow_zero):
        bound = "at least 0" if allow_zero else "greater than 0"
        raise ValueError(f"{name.capitalize()} must be {bound} seconds, got {value!r}")
    if seconds > MAX_SECONDS:
        raise ValueError(f"{name.capitalize()} must be at most {MAX_SECONDS:g} seconds, got {value!r}")
    return seconds


def check_stop(value: Any) -> int:
    """Permutation limit: at least one target must be scanned."""
    return check_int("stop", value, 1, sys.maxsize)


def check_delay(value: Any) -> float:
    return check_seconds("delay", value, allow_zero=True)


def check_timeout(value: Any) -> float:
    return check_seconds("timeout", value, allow_zero=False)


def check_concurrency(value: Any) -> int:
    return check_int("concurrency", value, 1, MAX_CONCURRENCY)


def check_cross_depth(value: Any) -> int:
    """Rounds of link-following; ``run_cross_scan`` always runs at least one."""
    return check_int("cross depth", value, 1, MAX_CROSS_DEPTH)


def check_cross_sweep(value: Any) -> int:
    """Targets swept against every module; 0 disables sweeping."""
    return check_int("cross sweep", value, 0, MAX_CROSS_SWEEP)
