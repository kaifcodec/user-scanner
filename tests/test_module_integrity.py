import ast
import re
from collections import defaultdict
from pathlib import Path


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_no_duplicate_normalized_module_names():
    """
    Ensure no two scan modules share the same normalized name across any categories.
    For example: 'lnk_bio.py' vs 'lnkbio.py', or 'crates_io.py' vs 'cratesio.py'.
    """
    root = _get_project_root()

    for scan_type in ["user_scan", "email_scan"]:
        base_dir = root / "user_scanner" / scan_type
        assert base_dir.exists(), f"Directory not found: {base_dir}"

        normalized_map = defaultdict(list)
        for path in base_dir.rglob("*.py"):
            if path.name.startswith("__"):
                continue

            # Normalized name strips underscores, hyphens, dots
            norm_name = re.sub(r"[^a-z0-9]", "", path.stem.lower())
            rel_path = path.relative_to(base_dir).as_posix()
            normalized_map[norm_name].append(rel_path)

        duplicates = {k: v for k, v in normalized_map.items() if len(v) > 1}
        assert not duplicates, (
            f"Duplicate or similarly-named modules found in {scan_type}:\n"
            + "\n".join(f"  - '{k}': {', '.join(paths)}" for k, paths in duplicates.items())
        )


def test_no_duplicate_validator_functions():
    """
    Ensure every validator function `validate_<name>` is unique when normalized.
    Catches cases where two modules export conflicting validator functions.
    """
    root = _get_project_root()

    for scan_type in ["user_scan", "email_scan"]:
        base_dir = root / "user_scanner" / scan_type
        validator_map = defaultdict(list)

        for path in base_dir.rglob("*.py"):
            if path.name.startswith("__"):
                continue

            rel_path = path.relative_to(base_dir).as_posix()
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("validate_"):
                        norm_val = re.sub(r"[^a-z0-9]", "", node.name.removeprefix("validate_").lower())
                        validator_map[norm_val].append((node.name, rel_path))
            except Exception as e:
                raise AssertionError(f"Failed to parse AST for {path}: {e}")

        duplicates = {k: v for k, v in validator_map.items() if len(v) > 1}
        assert not duplicates, (
            f"Conflicting validator functions found in {scan_type}:\n"
            + "\n".join(
                f"  - Normalized '{k}': " + ", ".join(f"{fn}() in {p}" for fn, p in occurrences)
                for k, occurrences in duplicates.items()
            )
        )


def test_no_duplicate_show_urls_in_user_scan():
    """
    Ensure no two user_scan modules target the exact same public profile `show_url` pattern.
    Prevents adding duplicate platforms with arbitrary different file names.
    """
    root = _get_project_root()
    base_dir = root / "user_scanner" / "user_scan"
    show_url_map = defaultdict(list)

    for path in base_dir.rglob("*.py"):
        if path.name.startswith("__"):
            continue

        rel_path = path.relative_to(base_dir).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "show_url":
                            url_val = ""
                            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                url_val = node.value.value
                            elif isinstance(node.value, ast.JoinedStr):
                                parts = []
                                for part in node.value.values:
                                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                                        parts.append(part.value)
                                    elif isinstance(part, ast.FormattedValue):
                                        parts.append("{user}")
                                url_val = "".join(parts)

                            if url_val and url_val.startswith(("http://", "https://")):
                                # Normalize user placeholder and trailing slashes
                                norm_url = re.sub(r"\{.*?\}", "{user}", url_val).rstrip("/").lower()
                                show_url_map[norm_url].append(rel_path)
        except Exception as e:
            raise AssertionError(f"Failed to parse AST for {path}: {e}")

    # Flag identical public profile URLs
    duplicates = {k: v for k, v in show_url_map.items() if len(v) > 1}
    assert not duplicates, (
        "Duplicate target show_url patterns found across user_scan modules:\n"
        + "\n".join(f"  - '{url}': {', '.join(paths)}" for url, paths in duplicates.items())
    )
