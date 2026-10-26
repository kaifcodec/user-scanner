import math
import sys

import pytest

from user_scanner.core import limits

INVALID_FLOATS = ["nan", "inf", "-inf", float("nan"), float("inf"), math.inf]


@pytest.mark.parametrize(
    "check, valid",
    [
        (limits.check_stop, [1, "1", 100, sys.maxsize]),
        (limits.check_concurrency, [1, "1", 60, limits.MAX_CONCURRENCY]),
        (limits.check_cross_depth, [1, "1", limits.MAX_CROSS_DEPTH]),
        (limits.check_cross_sweep, [0, "0", 3, limits.MAX_CROSS_SWEEP]),
    ],
)
def test_int_options_accept_their_valid_range(check, valid):
    for value in valid:
        assert check(value) == int(value)


@pytest.mark.parametrize(
    "check, too_small",
    [
        (limits.check_stop, [0, -1, "0", "-5"]),
        (limits.check_concurrency, [0, -1, "-10"]),
        (limits.check_cross_depth, [0, -1, "-5"]),
        (limits.check_cross_sweep, [-1, "-2"]),
    ],
)
def test_int_options_reject_values_below_their_minimum(check, too_small):
    for value in too_small:
        with pytest.raises(ValueError, match="must be at least"):
            check(value)


@pytest.mark.parametrize(
    "check",
    [limits.check_stop, limits.check_concurrency, limits.check_cross_depth, limits.check_cross_sweep],
)
def test_int_options_reject_non_integers(check):
    for value in ["abc", "", None, "1.5", 2.7, True, False, *INVALID_FLOATS]:
        with pytest.raises(ValueError):
            check(value)


def test_cross_scan_knobs_have_a_maximum():
    for value in [limits.MAX_CROSS_DEPTH + 1, 10_000]:
        with pytest.raises(ValueError, match="must be at most 5"):
            limits.check_cross_depth(value)
    for value in [limits.MAX_CROSS_SWEEP + 1, 10_000]:
        with pytest.raises(ValueError, match="must be at most 20"):
            limits.check_cross_sweep(value)


def test_concurrency_has_a_maximum():
    for value in [limits.MAX_CONCURRENCY + 1, 10_000, 10**18, str(10**18)]:
        with pytest.raises(ValueError, match="must be at most 500"):
            limits.check_concurrency(value)


def test_stop_rejects_values_islice_cannot_take():
    with pytest.raises(ValueError, match="must be at most"):
        limits.check_stop(sys.maxsize + 1)


def test_integral_float_is_accepted_as_int():
    assert limits.check_concurrency(4.0) == 4


def test_delay_accepts_zero_and_bounded_values():
    for value in [0, "0", 0.0, 0.5, "2", limits.MAX_SECONDS]:
        assert limits.check_delay(value) == float(value)


def test_timeout_accepts_positive_bounded_values():
    for value in [0.1, "1", 15, limits.MAX_SECONDS]:
        assert limits.check_timeout(value) == float(value)


@pytest.mark.parametrize("check", [limits.check_delay, limits.check_timeout])
def test_seconds_reject_non_finite_values(check):
    for value in INVALID_FLOATS:
        with pytest.raises(ValueError, match="finite"):
            check(value)


@pytest.mark.parametrize("check", [limits.check_delay, limits.check_timeout])
def test_seconds_reject_negative_and_huge_values(check):
    for value in [-1, "-0.5", -1e-9]:
        with pytest.raises(ValueError, match="at least 0|greater than 0"):
            check(value)
    for value in [limits.MAX_SECONDS + 1, "1e9", 1e300]:
        with pytest.raises(ValueError, match="at most"):
            check(value)


def test_timeout_rejects_zero_but_delay_allows_it():
    with pytest.raises(ValueError, match="greater than 0"):
        limits.check_timeout(0)
    assert limits.check_delay(0) == 0.0


@pytest.mark.parametrize("check", [limits.check_delay, limits.check_timeout])
def test_seconds_reject_non_numbers(check):
    for value in ["abc", "", None, True]:
        with pytest.raises(ValueError, match="Invalid"):
            check(value)
