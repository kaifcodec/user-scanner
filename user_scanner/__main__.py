import argparse
import json
import sys
import os
import time

from colorama import Fore, Style
from itertools import islice
from dataclasses import replace

from user_scanner.cli.banner import print_banner
from user_scanner.core import formatter
from user_scanner.core.cross_scan import (
    DEFAULT_DEPTH,
    DEFAULT_SWEEP,
    EMAIL_CHOICES,
    LINK_CHOICES,
    CrossScanConfig,
    run_cross_scan,
)
from user_scanner.core.email_orchestrator import (
    run_email_category_batch,
    run_email_full_batch,
    run_email_module_batch,
)
from user_scanner.core.helpers import (
    ScanConfig,
    find_module,
    get_proxy_count,
    get_site_name,
    is_loud,
    is_valid_email,
    load_categories,
    load_modules,
    set_proxy_manager,
    find_category,
)
from user_scanner.core.orchestrator import (
    run_user_category,
    run_user_full,
    run_user_module,
)
from user_scanner.core.result import Result, Status
from user_scanner.core.version import load_local_version
from user_scanner.core.hudson import run_hudson_scan
from user_scanner.utils.update import update_self
from user_scanner.utils.updater_logic import check_for_updates
from user_scanner.core.loud_prompt import check_loud_module_permission
from user_scanner.core.patterns import expand_patterns_random, count_patterns

# Color configs
R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN
Y = Fore.YELLOW
X = Fore.RESET

MAX_PERMUTATIONS_LIMIT = 100


def _csv_names(value) -> tuple:
    """Split a repeatable, comma-separated -m/-c value into names."""
    if not value:
        return ()
    raw = ",".join(value) if isinstance(value, list) else value
    return tuple(name.strip() for name in raw.split(",") if name.strip())


def main():
    if "--only-found" in sys.argv:
        print(f"{Fore.YELLOW}[!] The '--only-found' flag is deprecated and has been removed.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Showing only found modules is now the DEFAULT behavior.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] To show all results, use the '--all' flag.{Style.RESET_ALL}")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        prog="user-scanner",
        description="Scan usernames or emails across multiple platforms.",
    )

    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument("-u", "--username", help="Username to scan across platforms")
    group.add_argument("-e", "--email", help="Email to scan across platforms")

    group.add_argument(
        "-uf", "--username-file", help="File containing usernames (one per line)"
    )
    group.add_argument(
        "-ef", "--email-file", help="File containing emails (one per line)"
    )

    parser.add_argument("-c", "--category", nargs="+", help="Scan all platforms in a category (comma-separated for multiple)")

    parser.add_argument("-m", "--module", nargs="+", help="Scan a specific module (comma-separated for multiple)")

    parser.add_argument(
        "-lu",
        "--list-user",
        action="store_true",
        help="List all available modules for username scanning",
    )

    parser.add_argument(
        "-le",
        "--list-email",
        action="store_true",
        help="List all available modules for email scanning",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output to show urls of the websites",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all results including Not Found/Not Registered/Error/Skipped.",
    )

    parser.add_argument(
        "-s",
        "--stop",
        type=int,
        default=MAX_PERMUTATIONS_LIMIT,
        help="Limit permutations",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        help="Override default request timeout in seconds",
    )

    parser.add_argument(
        "-C",
        "--concurrency",
        type=int,
        help="Override default concurrency limit (default: 60 for username, 25 for email scan)",
    )

    parser.add_argument(
        "-d", "--delay", type=float, default=0, help="Delay between requests"
    )

    parser.add_argument("-f", "--format", choices=["csv", "json", "pdf"], help="Output format")

    parser.add_argument(
        "--no-pdf-media",
        action="store_true",
        help="Disable profile photo media fetching in PDF report generation",
    )

    parser.add_argument("-o", "--output", type=str, help="Output file path")

    parser.add_argument(
        "-P",
        "--proxy-file",
        type=str,
        help="Path to proxy list file (one proxy per line)",
    )

    parser.add_argument(
        "--validate-proxies",
        action="store_true",
        help="Validate proxies before scanning (tests against gstatic.com/generate_204)",
    )

    parser.add_argument(
        "--allow-loud",
        action="store_true",
        help="Enable scanning sites that may send emails/notifications "
        "(password resets, etc.)",
    )

    parser.add_argument(
        "--no-nsfw",
        action="store_true",
        help="Disable NSFW site scanning",
    )

    parser.add_argument(
        "--cross-scan",
        action="store_true",
        help="After the scan, follow the usernames, links and email addresses its "
        "results expose and scan those too",
    )

    parser.add_argument(
        "--cross-links",
        choices=list(LINK_CHOICES),
        default="all",
        help="Which links a cross-scan may pivot from: all, verified "
        "(platform-proven connections only), or none (site-reported handles only)",
    )

    parser.add_argument(
        "--cross-emails",
        choices=list(EMAIL_CHOICES),
        default="verified",
        help="Which addresses found in scan metadata a cross-scan may scan as emails: "
        "all (including ones scraped from bio text), verified (only addresses a site "
        "published in its own email field), or none. Loud email modules are skipped "
        "unless --allow-loud (default: verified)",
    )

    parser.add_argument(
        "--cross-depth",
        type=int,
        default=DEFAULT_DEPTH,
        help="Rounds of link-following. Each round pivots off the accounts the previous "
        f"one found, reaching handles only a chain of links names (default: {DEFAULT_DEPTH})",
    )

    parser.add_argument(
        "--cross-sweep",
        type=int,
        default=DEFAULT_SWEEP,
        metavar="N",
        help="Targets — usernames and addresses together — a cross-scan sweeps against "
        "every module of their kind, across all rounds. 0 disables sweeping, leaving only "
        "the sites a pivot named — fewer accounts, but no handle collisions "
        f"(default: {DEFAULT_SWEEP})",
    )

    parser.add_argument("-U", "--update", action="store_true", help="Update the tool")

    parser.add_argument(
        "--hudson", "--hudson-scan",
        action="store_true",
        dest="hudson_scan",
        help="Check for infostealer intelligence using Hudson Rock's API",
    )


    parser.add_argument("--version", action="store_true", help="Print version")

    args = parser.parse_args()

    if args.timeout is not None:
        from user_scanner.core.helpers import set_global_timeout
        set_global_timeout(args.timeout)

    if args.concurrency is not None:
        from user_scanner.core.email_orchestrator import set_concurrency as set_email_concurrency
        from user_scanner.core.orchestrator import set_concurrency as set_user_concurrency
        set_email_concurrency(args.concurrency)
        set_user_concurrency(args.concurrency)

    if args.update:
        update_self()
        print(f"[{G}+{X}] {G}Update successful. Please restart the tool.{X}")
        sys.exit(0)

    if args.version:
        version, _ = load_local_version()
        print(f"user-scanner current version -> {G}{version}{X}")
        sys.exit(0)

    if args.list_user or args.list_email:
        categories = load_categories(args.list_email, args.no_nsfw)
        sorted_cats = sorted(categories.items(), key=lambda x: x[0].lower())
        try:
            import math
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table
            from rich import box

            console = Console()
            num_grid_cols = 1 if console.width < 70 else (3 if console.width >= 140 else 2)

            cat_panels = []
            total_modules = 0

            for cat_name, cat_path in sorted_cats:
                modules = load_modules(cat_path)
                sorted_mods = sorted(modules, key=lambda m: get_site_name(m).lower())
                total = len(sorted_mods)
                total_modules += total

                num_internal_cols = 2 if total > 8 else 1

                inner_table = Table.grid(expand=True, padding=(0, 1))
                for _ in range(num_internal_cols):
                    inner_table.add_column(ratio=1)

                rows = math.ceil(total / num_internal_cols)
                for r in range(rows):
                    row_cells = []
                    for c in range(num_internal_cols):
                        idx = r + c * rows
                        if idx < total:
                            mod = sorted_mods[idx]
                            name = get_site_name(mod)
                            loud = " [bold red](loud)[/bold red]" if is_loud(name, is_email=args.list_email) else ""
                            row_cells.append(f"[white]• {name}[/white]{loud}")
                        else:
                            row_cells.append("")
                    inner_table.add_row(*row_cells)

                p = Panel(
                    inner_table,
                    title=f"[bold magenta]== {cat_name.upper()} ({total}) ==[/bold magenta]",
                    title_align="left",
                    border_style="cyan",
                    box=box.ROUNDED,
                    padding=(0, 1),
                )
                cat_panels.append(p)

            scan_label = "Email" if args.list_email else "User"
            console.print(f"\n[bold cyan]{scan_label} Modules & Categories[/bold cyan] [dim]({total_modules} modules across {len(categories)} categories)[/dim]\n")

            grid = Table.grid(expand=True, padding=(0, 1))
            for _ in range(num_grid_cols):
                grid.add_column(ratio=1)

            for i in range(0, len(cat_panels), num_grid_cols):
                row_panels = [cat_panels[i + c] if i + c < len(cat_panels) else "" for c in range(num_grid_cols)]
                grid.add_row(*row_panels)

            console.print(grid)
            console.print()
        except ImportError:
            for cat_name, cat_path in sorted_cats:
                modules = load_modules(cat_path)
                sorted_mods = sorted(modules, key=lambda m: get_site_name(m).lower())
                print(Fore.MAGENTA + f"\n== {cat_name.upper()} SITES =={Style.RESET_ALL}")
                for module in sorted_mods:
                    name = get_site_name(module)
                    loud = (
                        f" {R}(loud){X}" if is_loud(name, is_email=args.list_email) else ""
                    )
                    print(f"  - {name}{loud}")
        return

    if not (args.username or args.email or args.username_file or args.email_file):
        parser.print_help()
        return

    if args.output and not args.format:
        ext = args.output.lower()
        if ext.endswith('.json'):
            args.format = 'json'
        elif ext.endswith('.csv'):
            args.format = 'csv'
        elif ext.endswith('.pdf'):
            args.format = 'pdf'
        else:
            print(f"\n{Fore.RED}[✘] Specify output format using -f (json, csv, pdf) or use a known file extension.{Style.RESET_ALL}")
            sys.exit(1)

    # Initialize proxy manager if proxy file is provided
    if args.proxy_file:
        try:
            # Validate proxies if flag is set
            if args.validate_proxies:
                print(f"{C}[*] Validating proxies from {args.proxy_file}...{X}")
                from user_scanner.core.helpers import ProxyManager, validate_proxies

                # Load proxies first
                temp_manager = ProxyManager(args.proxy_file)
                all_proxies = temp_manager.proxies
                print(f"{C}[*] Testing {len(all_proxies)} proxies...{X}")

                # Validate them
                working_proxies = validate_proxies(all_proxies)

                if not working_proxies:
                    print(f"{R}[✘] No working proxies found{X}")
                    sys.exit(1)

                print(
                    f"{G}[+] Found {len(working_proxies)} working proxies out of {len(all_proxies)}{X}"
                )

                set_proxy_manager(proxies=working_proxies)
                proxy_count = get_proxy_count()
                print(f"{G}[+] Using {proxy_count} validated proxies{X}")
            else:
                set_proxy_manager(args.proxy_file)
                proxy_count = get_proxy_count()
                print(f"{G}[+] Loaded {proxy_count} proxies from {args.proxy_file}{X}")
        except Exception as e:
            print(f"{R}[✘] Error loading proxies: {e}{X}")
            sys.exit(1)

    check_for_updates()
    print_banner()


    # Handle bulk email file
    if args.email_file:
        try:
            with open(args.email_file, "r", encoding="utf-8") as f:
                emails = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]

            # Validate email formats
            valid_emails = []
            for email in emails:
                if is_valid_email(email):
                    valid_emails.append(email)
                else:
                    print(f"{Y}[!] Skipping invalid email format: {email}{X}")

            if not valid_emails:
                print(f"{R}[✘] Error: No valid emails found in {args.email_file}{X}")
                sys.exit(1)

            print(
                f"{C}[+] Loaded {len(valid_emails)} {'email' if len(valid_emails) == 1 else 'emails'} from {args.email_file}{X}"
            )
            is_email = True
            targets_found = valid_emails
        except FileNotFoundError:
            print(f"{R}[✘] Error: File not found: {args.email_file}{X}")
            sys.exit(1)
        except Exception as e:
            print(f"{R}[✘] Error reading email file: {e}{X}")
            sys.exit(1)
    # Handle bulk username file
    elif args.username_file:
        try:
            with open(args.username_file, "r", encoding="utf-8") as f:
                usernames = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
            if not usernames:
                print(
                    f"{R}[✘] Error: No valid usernames found in {args.username_file}{X}"
                )
                sys.exit(1)
            print(
                f"{C}[+] Loaded {len(usernames)} {'username' if len(usernames) == 1 else 'usernames'} from {args.username_file}{X}"
            )
            is_email = False
            targets_found = usernames
        except FileNotFoundError:
            print(f"{R}[✘] Error: File not found: {args.username_file}{X}")
            sys.exit(1)
        except Exception as e:
            print(f"{R}[✘] Error reading username file: {e}{X}")
            sys.exit(1)
    else:
        is_email = args.email is not None
        if is_email and not is_valid_email(args.email):
            print(R + "[✘] Error: Invalid email format." + X)
            sys.exit(1)

        target_name = args.username or args.email
        targets_found = [target_name]

    # Handle permutations (only for single username/email)

    targets = []
    for target_name in targets_found:
        temp_targets = list(islice(expand_patterns_random(target_name), args.stop))
        targets.extend(temp_targets)
        if len(temp_targets) > 1:
            total = count_patterns(target_name)
            if total > len(temp_targets):
                print(
                    C + f"[+] Scanning {len(temp_targets)} of {total} permutations" + Style.RESET_ALL
                )
            else:
                print(
                    C + f"[+] Scanning {len(temp_targets)} permutations" + Style.RESET_ALL
                )

    results = []
    show_all = args.all
    if args.module and not args.all:
        raw_module_str = ",".join(args.module) if isinstance(args.module, list) else args.module
        requested_modules = [m.strip() for m in raw_module_str.split(",") if m.strip()]
        if len(requested_modules) <= 10:
            show_all = True

    config = ScanConfig(
        allow_loud=args.allow_loud,
        show_all=show_all,
        no_nsfw=args.no_nsfw,
        verbose=args.verbose,
        timeout=args.timeout,
    )

    validated_modules = []
    validated_categories = []

    if args.hudson_scan:
        if args.cross_scan:
            print(f"{R}[✘] Error: --cross-scan cannot be used with --hudson {X}")
            sys.exit(1)
        if args.category or args.module:
            print(f"{R}[✘] Error: --hudson cannot be used with -m or -c {X}")
            print(f"{Y}[i] Use it independently{X}")
            sys.exit(1)
    else:
        if args.module:
            raw_module_str = ",".join(args.module) if isinstance(args.module, list) else args.module
            requested_modules = [m.strip() for m in raw_module_str.split(",") if m.strip()]
            
            if not requested_modules:
                print(R + f"[✘] Error: No valid {'email' if is_email else 'user'} modules specified." + Style.RESET_ALL)
                sys.exit(1)

            for m in requested_modules:
                found = find_module(m.replace(".", "_"), is_email, args.no_nsfw)
                if not found:
                    print(
                        R
                        + f"[✘] Error: {'Email' if is_email else 'User'} module '{m}' not found."
                        + Style.RESET_ALL
                    )
                    sys.exit(1)
                validated_modules.extend(found)
        elif args.category:
            raw_category_str = ",".join(args.category) if isinstance(args.category, list) else args.category
            requested_categories = [c.strip() for c in raw_category_str.split(",") if c.strip()]
            
            if not requested_categories:
                print(R + f"[✘] Error: No valid {'email' if is_email else 'user'} categories specified." + Style.RESET_ALL)
                sys.exit(1)

            categories_dict = load_categories(is_email, args.no_nsfw)
            for c in requested_categories:
                cat_path = categories_dict.get(c)
                if not cat_path:
                    print(
                        R
                        + f"[✘] Error: {'Email' if is_email else 'User'} category '{c}' not found."
                        + Style.RESET_ALL
                    )
                    sys.exit(1)
                validated_categories.append(cat_path)

    for i, target in enumerate(targets):
        target_results = []
        if i != 0 and args.delay:
            time.sleep(args.delay)

        if is_email:
            print(f"\n{Fore.CYAN} Checking email: {target}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.CYAN} Checking username: {target}{Style.RESET_ALL}")


        if args.hudson_scan:
            run_hudson_scan(target, is_email)
            continue


        if args.module:
            fn = run_email_module_batch if is_email else run_user_module
            modules_to_run = []
            for module in validated_modules:
                site_name = get_site_name(module)
                if not config.allow_loud and is_loud(site_name, is_email):
                    if not check_loud_module_permission(site_name, target):
                        skipped = Result.skipped().update(
                            site_name=site_name,
                            username=target,
                            category=find_category(module) or "Unknown",
                            is_email=is_email,
                        )
                        skipped.show(config)
                        target_results.append(skipped)
                        continue
                    per_module_config = replace(config, allow_loud=True)
                    target_results.extend(fn(module, target, per_module_config))
                else:
                    modules_to_run.append(module)

            if modules_to_run:
                target_results.extend(fn(modules_to_run, target, config))

        elif args.category:
            fn = run_email_category_batch if is_email else run_user_category
            for cat_path in validated_categories:
                target_results.extend(
                    fn(
                        cat_path,
                        target,
                        config,
                    )
                )
        else:
            fn = run_email_full_batch if is_email else run_user_full
            target_results.extend(fn(target, config))



        if args.cross_scan:
            target_results.extend(
                run_cross_scan(
                    target_results,
                    config,
                    CrossScanConfig(
                        links=args.cross_links,
                        emails=args.cross_emails,
                        sweep=args.cross_sweep,
                        depth=args.cross_depth,
                        modules=_csv_names(args.module),
                        categories=_csv_names(args.category),
                    ),
                )
            )
            
        for r in target_results:
            r.seed_target = target
            
        results.extend(target_results)
    if args.hudson_scan:
        sys.exit(0)

    is_pdf_export = args.format == "pdf" or (args.output and args.output.lower().endswith(".pdf"))

    if args.output or args.format:
        default_ext = args.format if args.format else "pdf"
        if is_pdf_export:
            default_ext = "pdf"
            
        output_path = args.output or f"{targets_found[0] if targets_found else 'target'}_report.{default_ext}"

        target_to_results = {}
        for r in results:
            t = getattr(r, "seed_target", None)
            if not t:
                t = getattr(r, "email", None) if is_email else getattr(r, "username", None)
            if not t:
                t = targets_found[0] if targets_found else "Target"
            if t not in target_to_results:
                target_to_results[t] = []
            target_to_results[t].append(r)
            
        for t, t_results in target_to_results.items():
            if len(target_to_results) > 1:
                if args.output:
                    base, ext = os.path.splitext(args.output)
                    t_output = f"{base}_{t}{ext}"
                else:
                    t_output = f"{t}_report.{default_ext}"
            else:
                t_output = output_path

            if is_pdf_export:
                version_str, _ = load_local_version()
                scan_type_str = "Email" if is_email else "Username"
                if args.cross_scan:
                    scan_type_str = f"Cross-Scan ({scan_type_str})"

                try:
                    pdf_bytes = formatter.into_pdf(
                        t_results,
                        target=t,
                        scan_type=scan_type_str,
                        total_modules=len(t_results),
                        include_media=not args.no_pdf_media,
                        version=version_str,
                    )
                    with open(t_output, "wb") as f:
                        f.write(pdf_bytes)
                    print(G + f"\n[+] PDF report saved to {t_output}" + Style.RESET_ALL)
                except ImportError as e:
                    print(f"\n{R}[✘] PDF export failed for {t}: {e}{X}")
                except Exception as e:
                    print(f"\n{R}[✘] Failed to generate PDF report for {t}: {e}{X}")

            elif args.format == "json":
                new_items = formatter.get_json_data(t_results)
                data = []

                if os.path.exists(t_output):
                    try:
                        with open(t_output, "r", encoding="utf-8") as f:
                            old = json.load(f)
                            if isinstance(old, list):
                                data = old
                    except (json.JSONDecodeError, Exception):
                        pass

                data.extend(new_items)
                with open(t_output, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(G + f"\n[+] JSON Results saved to {t_output}" + Style.RESET_ALL)

            elif args.format == "csv":
                content_csv = formatter.into_csv(t_results)
                try:
                    with open(t_output, "r", encoding="utf-8") as init_file:
                        has_content = init_file.read().strip() != ""
                except Exception:
                    has_content = False

                with open(t_output, "a", encoding="utf-8") as f:
                    if has_content:
                        f.write("\n")
                    f.write(content_csv)
                print(G + f"\n[+] CSV Results saved to {t_output}" + Style.RESET_ALL)


    total_found = len([r for r in results if r.is_found()])
    total_skipped = len([r for r in results if r.status == Status.SKIPPED])

    if not config.show_all and total_found == 0 and total_skipped == 0:
        print(f"\n{R}[✘] No results found for the given target(s).{X}")
    else:
        print(f"\n{C}[i] Scan complete.\n  Total hits:{X} {total_found}")
        if total_skipped > 0:
            print(f"  {C}Skipped:{X} {total_skipped}")
            print(f"  {Y}Reason for skip: Module(s) notify{X} (but only if target exists there) {Y}the target with password reset email(s){X}")
            print(f"  {Y}Use {G}--allow-loud{X}{Y} to include those module(s) to be scanned{X}")

if __name__ == "__main__":
    main()
