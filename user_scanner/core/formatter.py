import json
from typing import List

from user_scanner.core.result import CSV_FIELDS, Result

INDENT = "  "
CSV_HEADER = ",".join(CSV_FIELDS)


def indentate(msg: str, indent: int):
    if indent <= 0:
        return msg
    tabs = INDENT * indent
    return "\n".join([f"{tabs}{line}" for line in msg.split("\n")])


def into_json(results: List[Result]) -> str:
    return json.dumps([r.to_dict() for r in results], indent=4)


def get_json_data(results: List[Result]) -> list:
    """Returns a list of dictionaries ready for JSON serialization."""
    return [r.to_dict() for r in results]


def into_csv(results: List[Result]) -> str:
    return CSV_HEADER + "\n" + "\n".join(result.to_csv() for result in results)
