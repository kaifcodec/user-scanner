from user_scanner.core.result import Result
from typing import List

INDENT = "  "
CSV_HEADER = "username,category,site_name,status,reason"


def indentate(msg: str, indent: int):
    if indent <= 0:
        return msg
    tabs = INDENT * indent
    return "\n".join([f"{tabs}{line}" for line in msg.split("\n")])


def into_json(results: List[Result]) -> str:
    res = "[\n"

    for i, result in enumerate(results):
        is_last = i == len(results) - 1
        end = "" if is_last else ","
        res += indentate(result.to_json().replace("\t", INDENT), 1) + end + "\n"

    return res + "]"


def into_csv(results: List[Result]) -> str:
    return CSV_HEADER + "\n" + "\n".join(result.to_csv() for result in results)
