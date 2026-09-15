"""
In-memory session manager for user-scanner web workbench.
Provides fast, safe, ephemeral storage for active scan findings and report downloads.
"""

from typing import Any, Optional

_SCAN_SESSIONS: dict[str, dict[str, Any]] = {}
_MAX_SESSIONS = 100


def get_scan_session(scan_id: str) -> Optional[dict[str, Any]]:
    """Retrieve scan findings and metadata for a given scan ID."""
    clean = (scan_id or "").strip()
    return _SCAN_SESSIONS.get(clean)


def save_scan_session(scan_id: str, data: dict[str, Any]) -> None:
    """Store scan findings in memory. Caps total stored sessions to prevent memory bloat."""
    clean = (scan_id or "").strip()
    if not clean or not data:
        return
    if len(_SCAN_SESSIONS) >= _MAX_SESSIONS:
        oldest_key = next(iter(_SCAN_SESSIONS))
        _SCAN_SESSIONS.pop(oldest_key, None)
    _SCAN_SESSIONS[clean] = data


def delete_scan_session(scan_id: str) -> None:
    """Remove a scan session from memory."""
    clean = (scan_id or "").strip()
    _SCAN_SESSIONS.pop(clean, None)


def get_all_scan_sessions() -> dict[str, dict[str, Any]]:
    """Return all active scan sessions."""
    return _SCAN_SESSIONS


# Backward-compatibility aliases
get_backup = get_scan_session
save_backup = save_scan_session
delete_backup = delete_scan_session
get_all_backups = get_all_scan_sessions
