"""Render untrusted scan data without letting it drive the terminal.

Usernames, emails, reasons, and profile fields are printed as-is today.
A value from a bulk file or a remote profile can carry ANSI, OSC 8 links,
carriage returns, backspaces, or bidi overrides. Those are removed here.
Rich markup in the same values is escaped only for Rich, so a bracket in
a username cannot close the progress bar's own style.
"""

import re

# Complete CSI and OSC sequences, then any leftover escape, C0/C1 control
# (tab and newline stay, so wrapped bios still wrap), and bidi/zero-width
# characters that reorder or hide the text around them.
_CONTROLS = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]"
    r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
    r"|\x1b[@-Z\\-_]"
    r"|[\x00-\x08\x0b-\x1f\x7f]"
    r"|[\u0080-\u009f]"
    r"|[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]"
)


def strip_terminal_controls(value: object) -> str:
    """Return ``value`` as text with terminal controls removed."""
    return _CONTROLS.sub("", str(value))


def rich_safe(value: object) -> str:
    """Text that is safe to interpolate into a Rich markup string."""
    from rich.markup import escape

    return escape(strip_terminal_controls(value))


def scanning_description(target: object, site: object | None = None) -> str:
    """Progress-bar description. The cyan style is ours; the words are not."""
    label = rich_safe(target)
    if site is None:
        return f"[cyan]Scanning {label}..."
    return f"[cyan]Scanning {label}... ({rich_safe(site)})"
