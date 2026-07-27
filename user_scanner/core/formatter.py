import json
from typing import List, Optional

from user_scanner.core.result import CSV_FIELDS, Result

CSV_HEADER = ",".join(CSV_FIELDS)


def into_json(results: List[Result]) -> str:
    return json.dumps([r.to_dict() for r in results], indent=4)


def get_json_data(results: List[Result]) -> list:
    """Returns a list of dictionaries ready for JSON serialization."""
    return [r.to_dict() for r in results]


def into_csv(results: List[Result]) -> str:
    return CSV_HEADER + "\n" + "\n".join(result.to_csv() for result in results)


def into_pdf(
    results: List[Result],
    target: str = "Target",
    scan_type: str = "Unknown",
    total_modules: Optional[int] = None,
    include_media: bool = True,
    version: Optional[str] = None,
) -> bytes:
    from user_scanner.core.pdf_generator import generate_pdf_report

    return generate_pdf_report(
        target=target,
        scan_type=scan_type,
        results=results,
        total_modules=total_modules,
        include_media=include_media,
        version=version,
    )

