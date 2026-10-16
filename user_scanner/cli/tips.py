"""CLI tips, intelligence service recommendations, and operational hints."""

from typing import Sequence

from colorama import Fore, Style

from user_scanner.core.result import Result, Status

_BLOCKED_KEYWORDS = (
    "403",
    "429",
    "waf",
    "cloudflare",
    "timed out",
    "timeout",
    "curl: (28)",
    "connection closed",
    "rate limit",
)

PROXY_SPONSOR_URL = "https://proxy-seller.com/?partner=A711D0DB08424F5A"
PROXY_PROMO_CODE = "KAIF15"


def print_proxy_tip(results: Sequence[Result], has_proxy: bool = False) -> None:
    """Surface regional / WAF blocks and recommend proxy routing if not already configured."""
    if has_proxy:
        return

    blocked_count = sum(
        1
        for r in results
        if r.status == Status.ERROR
        and any(kw in str(r.reason or "").lower() for kw in _BLOCKED_KEYWORDS)
    )

    if blocked_count > 0:
        Y = Fore.YELLOW
        G = Fore.GREEN
        C = Fore.CYAN
        B = Style.BRIGHT
        RESET = Style.RESET_ALL

        print(
            f"\n{Y}{B}[!] {blocked_count} site(s) were unreachable{RESET} due to regional blocks or rate limits {Y}(403/timeout){RESET}."
            f"\n    {C}{B}Tip:{RESET} Route scans with {G}{B}-P/--proxy-file{RESET} to get verdicts from blocked sites."
            f"\n    {B}Tested provider:{RESET} {C}{PROXY_SPONSOR_URL}{RESET} (use code {G}{B}{PROXY_PROMO_CODE}{RESET} for {G}{B}15% off{RESET})"
        )


def print_hudson_remediation_tip() -> None:
    """Print security guidance when infostealer compromises are detected."""
    Y = Fore.YELLOW
    B = Style.BRIGHT
    C = Fore.CYAN
    RESET = Style.RESET_ALL

    print(
        f"\n{Y}{B}[!] Security Notice:{RESET} All credentials saved on infected computers are at risk."
    )
    print(
        f"    {C}{B}Remediation tools:{RESET} Visit {C}https://www.hudsonrock.com/free-tools{RESET} for identity monitoring."
    )


def print_loud_skip_tip(skipped_count: int) -> None:
    """Explain why loud modules were skipped and how to enable them."""
    if skipped_count <= 0:
        return

    C = Fore.CYAN
    Y = Fore.YELLOW
    G = Fore.GREEN
    B = Style.BRIGHT
    RESET = Style.RESET_ALL

    print(f"  {C}Skipped:{RESET} {skipped_count}")
    print(
        f"  {Y}Reason for skip: Module(s) may notify the target with password reset emails.{RESET}"
    )
    print(
        f"  {Y}Use {G}{B}--allow-loud{RESET}{Y} to include those module(s) in the scan.{RESET}"
    )
