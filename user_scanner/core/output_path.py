"""Export paths that stay inside the directory the caller selected.

Bulk targets are untrusted input. A username such as ``../../chosen/path``
must never become a path segment, and a symlink planted inside the output
directory must not redirect a report onto a file outside it.
"""

import re
import unicodedata
from pathlib import Path

# After NFKC, only a single safe path segment remains. Slashes, controls,
# and other separators have already been folded into underscores.
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def slug_target(target: str, limit: int = 48) -> str:
    """Return a filename-safe slug. Never empty, never ``.`` or ``..``."""
    text = unicodedata.normalize("NFKC", str(target))
    text = text.replace("/", "_").replace("\\", "_")
    text = _UNSAFE.sub("_", text).strip("._")
    while ".." in text:
        text = text.replace("..", "_")
    text = text.strip("._")
    if not text:
        return "target"
    return text[:limit]


def export_path_for_target(
    *,
    requested: str | None,
    target: str,
    index: int,
    multiple: bool,
    default_ext: str,
) -> Path:
    """Path for one target's report.

    A caller-supplied path is used unchanged for a single target, because
    that path is the caller's choice. Every name derived from a target is a
    strict slug, and the resolved file must stay inside the output directory.
    """
    if requested and not multiple:
        return Path(requested)

    if requested:
        requested_path = Path(requested)
        root = requested_path.parent
        stem = requested_path.stem or "report"
        ext = requested_path.suffix or f".{default_ext}"
        filename = f"{stem}_{index:03d}_{slug_target(target)}{ext}"
    else:
        root = Path.cwd()
        slug = slug_target(target)
        if multiple:
            filename = f"report_{index:03d}_{slug}.{default_ext}"
        else:
            filename = f"{slug}_report.{default_ext}"

    return _contain(root, filename)


def _contain(root: Path, filename: str) -> Path:
    if filename != Path(filename).name or filename in {".", ".."}:
        raise ValueError(f"Refusing to write scan output to {filename!r}")
    base = root.resolve()
    candidate = (base / filename).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Refusing to write scan output outside {base}") from exc
    return candidate
