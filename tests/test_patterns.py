import pytest
from itertools import islice
from user_scanner.core.patterns import expand_patterns, expand_patterns_random, count_patterns


# ── expand_patterns: plain text (no pattern syntax) ──────────────────────

def test_plain_text():
    assert list(expand_patterns("john")) == ["john"]


def test_single_char():
    assert list(expand_patterns("x")) == ["x"]


def test_empty_input():
    assert list(expand_patterns("")) == [""]


# ── expand_patterns: charset basics ──────────────────────────────────────

def test_charset_range_letters():
    assert list(expand_patterns("[a-c]")) == ["a", "b", "c"]


def test_charset_range_digits():
    result = list(expand_patterns("[0-9]"))
    assert len(result) == 10
    assert result[0] == "0"
    assert result[-1] == "9"


def test_charset_single_char():
    assert list(expand_patterns("[a]")) == ["a"]


def test_charset_explicit_chars():
    result = list(expand_patterns("[abc]"))
    assert set(result) == {"a", "b", "c"}
    assert len(result) == 3


def test_charset_with_prefix():
    assert list(expand_patterns("john[a-c]")) == ["johna", "johnb", "johnc"]


def test_charset_with_suffix():
    assert list(expand_patterns("[a-c]xyz")) == ["axyz", "bxyz", "cxyz"]


def test_charset_with_prefix_and_suffix():
    result = list(expand_patterns("pre[a-c]post"))
    assert result == ["preapost", "prebpost", "precpost"]


def test_multiple_charsets():
    result = list(expand_patterns("[a-c][1-3]"))
    assert len(result) == 9
    assert result[0] == "a1"
    assert result[-1] == "c3"


def test_adjacent_charsets():
    result = set(expand_patterns("[ab][cd]"))
    assert result == {"ac", "ad", "bc", "bd"}


def test_charset_dash_literal():
    """A dash at the start of charset is treated as literal."""
    assert list(expand_patterns("[-]")) == ["-"]


def test_charset_mixed_range_and_literal():
    result = set(expand_patterns("[a-c0]"))
    assert result == {"a", "b", "c", "0"}


def test_charset_same_start_end():
    """[a-a] is equivalent to [a]."""
    assert list(expand_patterns("[a-a]")) == ["a"]


def test_charset_reversed_range():
    """Reversed range like [z-a] produces empty charset."""
    result = list(expand_patterns("[z-a]"))
    assert result == []


def test_reversed_range_with_text():
    """Empty charset causes no output even with surrounding text."""
    result = list(expand_patterns("pre[z-a]post"))
    assert result == []


# ── expand_patterns: lenset ──────────────────────────────────────────────

def test_lenset_single_value():
    result = list(expand_patterns("[ab]{2}"))
    assert result == ["aa", "ab", "ba", "bb"]


def test_lenset_range():
    result = list(expand_patterns("x[a-b]{0-1}"))
    # length 0: "" → "x", length 1: "a","b" → "xa","xb"
    assert result == ["x", "xa", "xb"]


def test_lenset_zero_only():
    """Length 0 produces a single empty expansion."""
    result = list(expand_patterns("x[a-z]{0}"))
    assert result == ["x"]


def test_lenset_semicolons():
    result = list(expand_patterns("x[ab]{1;3}"))
    # length 1: a, b (2) + length 3: 2^3 = 8 → total 10
    assert len(result) == 10
    assert "xa" in result
    assert "xb" in result
    assert "xaaa" in result
    assert "xbbb" in result


def test_lenset_large_range():
    result = list(expand_patterns("[a-z]{0-2}"))
    # length 0: 1 + length 1: 26 + length 2: 676 = 703
    assert len(result) == 703


def test_lenset_two_digit_combos():
    result = list(expand_patterns("x[0-9]{2}"))
    assert len(result) == 100
    assert result[0] == "x00"
    assert result[-1] == "x99"


def test_lenset_mixed_range_and_single():
    result = list(expand_patterns("[ab]{1;2-3}"))
    # length 1: 2 + length 2: 4 + length 3: 8 = 14
    assert len(result) == 14


def test_default_lenset_is_one():
    """Without {}, charset defaults to length 1."""
    assert list(expand_patterns("[abc]")) == list(expand_patterns("[abc]{1}"))


# ── expand_patterns: escaped characters ──────────────────────────────────

def test_escaped_open_bracket():
    assert list(expand_patterns("hello\\[world")) == ["hello[world"]


def test_escaped_close_bracket():
    assert list(expand_patterns("hello\\]world")) == ["hello]world"]


def test_escaped_backslash():
    assert list(expand_patterns("test\\\\")) == ["test\\"]


def test_escaped_bracket_pair():
    assert list(expand_patterns("a\\[b\\]c")) == ["a[b]c"]


def test_escape_inside_charset():
    """Backslash inside charset escapes the next character."""
    result = list(expand_patterns("[\\]]"))
    assert result == ["]"]


# ── expand_patterns: error cases ─────────────────────────────────────────

def test_error_unclosed_bracket():
    with pytest.raises(ValueError):
        list(expand_patterns("test[a-z"))


def test_error_unmatched_close_bracket():
    with pytest.raises(ValueError, match="unescaped"):
        list(expand_patterns("test]"))


def test_error_unclosed_brace():
    with pytest.raises(ValueError):
        list(expand_patterns("test[a]{1-3"))


def test_error_lone_open_bracket():
    with pytest.raises(ValueError):
        list(expand_patterns("["))


def test_error_lenset_starts_with_dash():
    with pytest.raises(ValueError):
        list(expand_patterns("[a]{-3}"))


# ── expand_patterns: complex / combined ──────────────────────────────────

def test_mixed_text_and_patterns():
    result = list(expand_patterns("pre[ab]{1-2}mid[xy]post"))
    # block1: a,b,aa,ab,ba,bb (6) × block2: x,y (2) = 12
    assert len(result) == 12
    assert "preamidxpost" in result
    assert "prebbmidypost" in result


def test_three_blocks():
    result = list(expand_patterns("[ab][12][xy]"))
    assert len(result) == 8  # 2 × 2 × 2
    assert "a1x" in result
    assert "b2y" in result


def test_pattern_is_iterator():
    """expand_patterns returns an iterator, not a list."""
    result = expand_patterns("[a-z]")
    assert hasattr(result, "__next__")


# ── expand_patterns_random ───────────────────────────────────────────────

def test_random_same_set():
    """Random expansion produces the same set of results."""
    pattern = "[a-c][1-3]"
    deterministic = set(expand_patterns(pattern))
    randomized = set(expand_patterns_random(pattern))
    assert deterministic == randomized


def test_random_same_count():
    pattern = "x[a-z]{0-2}"
    det_count = len(list(expand_patterns(pattern)))
    rand_count = len(list(expand_patterns_random(pattern)))
    assert det_count == rand_count


def test_random_plain_text():
    assert list(expand_patterns_random("hello")) == ["hello"]


def test_random_empty_input():
    assert list(expand_patterns_random("")) == [""]


def test_random_islice():
    """islice can limit the number of results from random expansion."""
    result = list(islice(expand_patterns_random("[a-z]{0-2}"), 10))
    assert len(result) == 10
    # All results should be unique
    assert len(set(result)) == 10


def test_random_reservoir_sampling():
    """When results exceed capacity, reservoir sampling is used.
    All items must still appear exactly once."""
    pattern = "[a-z]{1-2}"
    # 26 + 676 = 702 results, set capacity below that
    deterministic = set(expand_patterns(pattern))
    randomized = list(expand_patterns_random(pattern, capacity=50))
    assert set(randomized) == deterministic
    assert len(randomized) == len(deterministic)


def test_random_is_iterator():
    result = expand_patterns_random("[ab]")
    assert hasattr(result, "__next__")


# ── count_patterns ───────────────────────────────────────────────────────

def test_count_plain_text():
    assert count_patterns("john") == 1


def test_count_empty():
    assert count_patterns("") == 1


def test_count_charset():
    assert count_patterns("[a-z]") == 26


def test_count_with_lenset():
    # length 0: 1 + length 1: 26 + length 2: 676 = 703
    assert count_patterns("[a-z]{0-2}") == 703


def test_count_multiple_blocks():
    assert count_patterns("[a-c][0-9]") == 30  # 3 * 10


def test_count_matches_expansion():
    """count_patterns must match the actual number of expansions."""
    pattern = "pre[ab]{1-2}mid[xy]post"
    assert count_patterns(pattern) == len(list(expand_patterns(pattern)))
