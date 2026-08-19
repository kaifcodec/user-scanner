import html
import json
import re
from collections.abc import Iterator

_NEXT_PAGES_DATA_RE = re.compile(
    r'<script\b[^>]*\bid=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)
_NEXT_APP_FLIGHT_RE = re.compile(
    r'self\.__next_f\.push\(\s*\[\s*1\s*,\s*("(?:[^"\\]|\\.)*")\s*\]\s*\)'
)


def parse_next_pages_data(document: str) -> dict | None:
    """Return the Pages Router's embedded ``__NEXT_DATA__`` object."""
    match = _NEXT_PAGES_DATA_RE.search(document)
    if not match:
        return None

    payload = match.group(1)
    for candidate in (payload, html.unescape(payload)):
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        return data if isinstance(data, dict) else None

    return None


def iter_next_app_flight_chunks(document: str) -> Iterator[str]:
    """Yield decoded App Router Flight chunks embedded in a document."""
    for payload in _NEXT_APP_FLIGHT_RE.findall(document):
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(chunk, str):
            yield chunk


def parse_next_pages_redirect(page_props: dict) -> tuple[str, int] | None:
    """Return a Pages Router JSON redirect as ``(location, status)``."""
    location = page_props.get("__N_REDIRECT")
    status = page_props.get("__N_REDIRECT_STATUS")
    if isinstance(location, str) and type(status) is int:
        return location, status
    return None
