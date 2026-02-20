"""Tests for pattern expansion (PR #184 - Patterns feature)."""

import pytest
from user_scanner.core.patterns import (
    expand_patterns,
    expand_patterns_random,
    _char_range,
)


def test_plain_string_no_expansion():
    """Plain string without brackets yields only itself."""
    result = list(expand_patterns("john"))
    assert result == ["john"]


def test_single_char_set():
    """[a-c] yields a, b, c."""
    result = list(expand_patterns("[a-c]"))
    assert result == ["a", "b", "c"]


def test_username_with_single_digit():
    """john[0-9] yields john0, john1, ... john9."""
    result = list(expand_patterns("john[0-9]"))
    assert len(result) == 10
    assert "john0" in result
    assert "john9" in result
    assert "john" not in result


def test_username_with_two_digits():
    """john[0-9]{2} yields john00, john01, ... john99."""
    result = list(expand_patterns("john[0-9]{2}"))
    assert len(result) == 100
    assert "john00" in result
    assert "john99" in result


def test_length_range():
    """[0-9]{1-2} yields 1- and 2-digit combos."""
    result = list(expand_patterns("x[0-9]{1-2}"))
    assert "x0" in result
    assert "x99" in result
    assert len(result) == 10 + 100


def test_email_pattern():
    """Pattern works with emails: john[0-9]@mail.com."""
    result = list(expand_patterns("john[0-9]@mail.com"))
    assert "john0@mail.com" in result
    assert "john9@mail.com" in result
    assert len(result) == 10


def test_multiple_lengths_semicolon():
    """{1;2} yields length 1 and 2."""
    result = list(expand_patterns("x[a]{1;2}"))
    assert "xa" in result
    assert "xaa" in result
    assert len(result) == 2


def test_escape_bracket():
    """Escaped brackets are literal."""
    result = list(expand_patterns("john\\[0\\]"))
    assert result == ["john[0]"]


def test_char_range():
    """_char_range produces correct sequence."""
    assert _char_range("a", "c") == ["a", "b", "c"]
    assert _char_range("0", "2") == ["0", "1", "2"]


def test_invalid_unclosed_bracket():
    """Unclosed [ raises ValueError."""
    with pytest.raises(ValueError, match="Missing"):
        list(expand_patterns("john[0-9"))


def test_invalid_unescaped_bracket():
    """Standalone ] raises ValueError."""
    with pytest.raises(ValueError, match="Invalid"):
        list(expand_patterns("john]"))


def test_expand_patterns_random_yields_same_set():
    """Random order yields same elements as deterministic."""
    pattern = "user[0-9]{1}"
    deterministic = set(expand_patterns(pattern))
    random_order = set(expand_patterns_random(pattern))
    assert deterministic == random_order


def test_expand_patterns_random_different_order():
    """Random order differs from deterministic (with high probability)."""
    pattern = "x[abcdef]{2}"
    det = list(expand_patterns(pattern))
    rand1 = list(expand_patterns_random(pattern))
    rand2 = list(expand_patterns_random(pattern))
    assert set(det) == set(rand1) == set(rand2)
    # Very unlikely all three have identical order for 36 elements
    assert det != rand1 or rand1 != rand2


def test_parse_patterns_empty_returns_empty_list():
    """Empty input parses to blocks that yield empty string."""
    result = list(expand_patterns(""))
    assert result == [""]


def test_parse_patterns_combined():
    """Combined pattern: prefix[chars]{n}suffix."""
    result = list(expand_patterns("id[0-9]{2}x"))
    assert "id00x" in result
    assert "id99x" in result
    assert len(result) == 100
