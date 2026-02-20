"""
Pattern expansion for usernames and emails.

Replaces the legacy permutation system with a flexible pattern syntax:
- `[<chars>]` - Character set (e.g., [a-z], [0-9], [abc])
- `[<chars>]{<lens>}` - Character set with length spec (e.g., [0-9]{1;2} for 1 or 2 digits)
- Ranges: [a-z], [0-9]; multiple lengths: {1;2;3} or {1-3}
- Escaping: \\[, \\], \\\\ for literal brackets/backslash

Examples:
  john[a-z]       -> johna, johnb, ... johnz
  user[0-9]{1-2}  -> user0, user1, ... user99
  john\\.doe[0-9] -> john.doe0, john.doe1, ...
"""

import itertools
import random
from dataclasses import dataclass
from typing import Iterator, List, Set


@dataclass
class PatternBlock:
    """A parsed pattern block: charset and allowed lengths."""

    charset: List[str]
    lenset: List[int]


Block = str | PatternBlock


class Lexer:
    """Simple character-by-character lexer for pattern parsing."""

    def __init__(self, input_str: str) -> None:
        self.tokens = list(input_str)

    def peek(self) -> str:
        if self.tokens:
            return self.tokens[0]
        return ""

    def next_token(self) -> str:
        if self.tokens:
            return self.tokens.pop(0)
        return ""

    def parse_number(self) -> int | None:
        res: int | None = None
        while (char := self.peek()) and char in "0123456789":
            self.next_token()
            n = int(char)
            if res is not None:
                res = res * 10 + n
            else:
                res = n
        return res


def _char_range(start: str, end: str) -> List[str]:
    """Expand a character range (e.g., a-z, 0-9)."""
    return [chr(i) for i in range(ord(start), ord(end) + 1)]


def _parse_charset(lexer: Lexer) -> Set[str]:
    """Parse [ ... ] character set. Consumes the closing ]."""
    charset: Set[str] = set()

    while lexer.peek() != "]":
        cur = lexer.next_token()
        if not cur:
            raise ValueError('Missing \']\' at the end of pattern')

        if cur == "\\":
            nxt = lexer.next_token()
            if not nxt:
                raise ValueError('Invalid "\\" at end of pattern')
            charset.add(nxt)
        elif cur == "-":
            charset.add("-")
        else:
            if lexer.peek() == "-":
                lexer.next_token()
                other = lexer.next_token()
                if not other:
                    raise ValueError("Invalid range in pattern")
                charset.update(_char_range(cur, other))
            else:
                charset.add(cur)

    lexer.next_token()
    return charset


def _parse_lenset(lexer: Lexer) -> Set[int]:
    """Parse { ... } length set. Consumes the closing }.
    Supports: {1}, {1;2;3}, {1-3}"""
    lenset: Set[int] = set()
    NUMBERS = "0123456789"

    while (cur := lexer.peek()) != "}":
        if not cur:
            raise ValueError('Missing \'}\' at the end of pattern')

        if cur not in NUMBERS + "-" + ";":
            raise ValueError(f"Invalid character in length set: {cur!r}")

        if cur == "-":
            raise ValueError('Invalid "-" in length set')
        if cur in NUMBERS:
            lhs = lexer.parse_number()
            if lexer.peek() == "-":
                lexer.next_token()
                rhs = lexer.parse_number()
                if lhs is not None and rhs is not None:
                    for i in range(lhs, rhs + 1):
                        lenset.add(i)
            elif lhs is not None:
                lenset.add(lhs)
        else:
            lexer.next_token()

    lexer.next_token()
    return lenset


def _append_string(result: List[Block], new: str) -> None:
    """Append or concatenate to last string block."""
    if not result:
        result.append(new)
    elif isinstance(result[-1], str):
        result[-1] += new
    else:
        result.append(new)


def _parse_patterns(input_str: str) -> List[Block]:
    """Parse input into blocks (strings and PatternBlocks)."""
    lexer = Lexer(input_str)
    res: List[Block] = []

    while lexer.peek():
        cur = lexer.next_token()

        if cur == "\\":
            if lexer.peek() in ("[", "]", "\\"):
                _append_string(res, lexer.next_token())
            else:
                _append_string(res, cur)
        elif cur == "[":
            charset = _parse_charset(lexer)
            lenset: Set[int]
            if lexer.peek() == "{":
                lexer.next_token()
                lenset = _parse_lenset(lexer)
            else:
                lenset = {1}
            res.append(
                PatternBlock(charset=sorted(charset), lenset=sorted(lenset))
            )
        elif cur == "]":
            raise ValueError('Invalid unescaped \']\'')
        else:
            _append_string(res, cur)

    return res


def _iter_block(block: PatternBlock) -> Iterator[str]:
    """Yield all expansions of a PatternBlock."""
    for length in block.lenset:
        for combo in itertools.product(block.charset, repeat=length):
            yield "".join(combo)


def _iter_pattern(blocks: List[Block]) -> Iterator[str]:
    """Recursively yield all expansions of parsed blocks."""
    if not blocks:
        yield ""
        return

    first, *rest = blocks
    if isinstance(first, str):
        for suffix in _iter_pattern(rest):
            yield first + suffix
    else:
        for middle in _iter_block(first):
            for suffix in _iter_pattern(rest):
                yield middle + suffix


def expand_patterns(input_str: str) -> Iterator[str]:
    """
    Expand a pattern string into all possible values.

    Pattern syntax:
      [chars]       - single char from set (e.g. [a-z], [0-9])
      [chars]{n;m}  - 1 to m chars (e.g. [0-9]{1-2} for 1–2 digits)
    """
    blocks = _parse_patterns(input_str)
    yield from _iter_pattern(blocks)


def expand_patterns_random(
    input_str: str, capacity: int = 1000
) -> Iterator[str]:
    """
    Expand patterns and yield in random order.

    Useful to avoid predictable scan order (e.g. for rate-limit evasion).
    """
    patterns = list(expand_patterns(input_str))
    shuffled = list(patterns)
    random.shuffle(shuffled)
    yield from shuffled
