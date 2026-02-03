import itertools
from dataclasses import dataclass
from typing import List, Set


@dataclass
class PatternBlock:
    charset: List[str]
    lenset: List[int]


Block = str | PatternBlock


class Lexer:
    def __init__(self, input: str) -> None:
        self.tokens = [char for char in input]

    def peek(self) -> str:
        if self.tokens:
            return self.tokens[0]
        return ""

    def next(self) -> str:
        if self.tokens:
            return self.tokens.pop(0)
        return ""

    def parse_number(self) -> int | None:
        res = None
        while (next := self.peek()) and next in "0123456789":
            self.next()
            n = int(next)
            if res:
                res = res * 10 + n
            else:
                res = n

        return res


def _char_range(start: str, end: str) -> List[str]:
    return [chr(i) for i in range(ord(start), ord(end) + 1)]


def _parse_charset(lexer: Lexer) -> Set[str]:
    charset = set()

    while lexer.peek() != "]":
        cur = lexer.next()

        if not cur:
            raise ValueError('Missing "]" at the end of pattern')

        if cur == "\\":
            next = lexer.next()
            if not next:
                raise ValueError('Invalid "\\"')
            charset.add(next)

        elif cur == "-":
            charset.add(cur)
        else:
            if lexer.peek() == "-":
                lexer.next()
                other = lexer.next()

                if not other:
                    raise ValueError()

                charset.update(_char_range(cur, other))
            else:
                charset.add(cur)

    lexer.next()  # Remove "]"

    return charset


def _parse_lenset(lexer: Lexer) -> Set[int]:
    lenset = set()
    NUMBERS = "0123456789"

    while (cur := lexer.peek()) != "}":
        if not cur:
            raise ValueError('Missing "}" at the end of pattern')

        if cur not in NUMBERS + "-" + ";":
            raise ValueError(f"Invalid character: {cur}")

        elif cur == "-":
            raise ValueError('Invalid character at the lenset: "-"')
        elif cur in NUMBERS:
            lhs = lexer.parse_number()

            if lexer.peek() == "-":
                lexer.next()
                rhs = lexer.parse_number()

                if lhs is not None and rhs is not None:
                    for i in range(lhs, rhs + 1):
                        lenset.add(i)
            elif lhs is not None:
                lenset.add(lhs)
        else:
            lexer.next()

    lexer.next()  # Remove "}"

    return lenset


def _append_string(list: list, new: str):
    if not list:
        list.append(new)
    elif isinstance(list[-1], str):
        list[-1] += new
    else:
        list.append(new)


def _parse_patterns(input: str) -> List[Block]:
    lexer = Lexer(input)
    res: List[Block] = []

    while lexer.peek():
        cur = lexer.next()

        if cur == "\\":
            if lexer.peek() in ("[", "]", "\\"):
                _append_string(res, lexer.next())

        elif cur == "[":
            charset = _parse_charset(lexer)
            lenset = set()
            if lexer.peek() == "{":
                lexer.next()
                lenset = _parse_lenset(lexer)
            else:
                lenset.add(1)

            res.append(PatternBlock(charset=sorted(charset), lenset=sorted(lenset)))

        elif cur == "]":
            # Should already be handled by parse_charset,
            # therefore is invalid.
            raise ValueError('Invalid unscaped "]"')

        else:
            _append_string(res, cur)

    return res


def _iter_block(block: PatternBlock):
    for length in sorted(block.lenset):
        for combo in itertools.product(block.charset, repeat=length):
            yield "".join(combo)


def _iter_pattern(blocks: List[Block]):
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


def expand_patterns(input: str):
    blocks = _parse_patterns(input)
    yield from _iter_pattern(blocks)
