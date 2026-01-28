import argparse
import time
import sys
import re
from colorama import Fore, Style

from user_scanner.cli.banner import print_banner
from user_scanner.core.version import load_local_version
from user_scanner.core import formatter
from user_scanner.utils.updater_logic import check_for_updates
from user_scanner.utils.update import update_self

from user_scanner.core.helpers import (
    load_categories,
    load_modules,
    find_module,
    get_site_name,
    generate_permutations,
    set_proxy_manager,
    get_proxy_count
)

from user_scanner.core.orchestrator import (
    run_user_full,
    run_user_category,
    run_user_module
)

from user_scanner.core.email_orchestrator import (
    run_email_full_batch,
    run_email_category_batch,
    run_email_module_batch
)

# Color configs
R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN
Y = Fore.YELLOW
X = Fore.RESET

MAX_PERMUTATIONS_LIMIT = 100


def main():
    parser = argparse.ArgumentParser(
        prog="user-scanner",
        description="Scan usernames or emails across multiple platforms."
    )

    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument("-u", "--username",
                       help="Username to scan across platforms")
    group.add_argument("-e", "--email", help="Email to scan across platforms")

    group.add_argument("-uf", "--username-file",
                       help="File containing usernames (one per line)")
    group.add_argument("-ef", "--email-file",
                       help="File containing emails (one per line)")

    parser.add_argument("-c", "--category",
                        help="Scan all platforms in a category")

    parser.add_argument("-m", "--module", help="Scan a single specific module")


    parser.add_argument("-lu", "--list-user", action="store_true",
                        help="List all available modules for username scanning")

    parser.add_argument("-le", "--list-email", action="store_true",
                        help="List all available modules for email scanning")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output")

    parser.add_argument("-p", "--permute", type=str,
                        help="Generate permutations using a pattern")

    parser.add_argument("-s", "--stop", type=int,
                        default=MAX_PERMUTATIONS_LIMIT, help="Limit permutations")

    parser.add_argument("-d", "--delay", type=float,
                        default=0, help="Delay between requests")

    parser.add_argument(
        "-f", "--format", choices=["csv", "json"], help="Output format")

    parser.add_argument("-o", "--output", type=str, help="Output file path")

    parser.add_argument(
        "-P", "--proxy-file", type=str, help="Path to proxy list file (one proxy per line)")

    parser.add_argument(
        "--validate-proxies", action="store_true", 
        help="Validate proxies before scanning (tests against google.com)")

    parser.add_argument(
        "-U", "--update", action="store_true", help="Update the tool")

    parser.add_argument("--version", action="store_true", help="Print version")

    args = parser.parse_args()

    if args.update:
        update_self()
        print(f"[{G}+{X}] {G}Update successful. Please restart the tool.{X}")
        sys.exit(0)

    if args.version:
        version, _ = load_local_version()
        print(f"user-scanner current version -> {G}{version}{X}")
        sys.exit(0)

    if args.list_user:
        categories = load_categories()
        for cat_name, cat_path in categories.items():
            modules = load_modules(cat_path)
            print(Fore.MAGENTA +
                  f"\n== {cat_name.upper()} SITES =={Style.RESET_ALL}")
            for module in modules:
                print(f"  - {get_site_name(module)}")
        return

    if args.list_email:
        categories = load_categories(is_email=True)
        for cat_name, cat_path in categories.items():
            modules = load_modules(cat_path)
            print(Fore.MAGENTA +
                  f"\n== {cat_name.upper()} SITES =={Style.RESET_ALL}")
            for module in modules:
                print(f"  - {get_site_name(module)}")
        return

    if not (args.username or args.email or args.username_file or args.email_file):
        parser.print_help()
        return

    # Initialize proxy manager if proxy file is provided
    if args.proxy_file:
        try:
            # Validate proxies if flag is set
            if args.validate_proxies:
                print(f"{C}[*] Validating proxies from {args.proxy_file}...{X}")
                from user_scanner.core.helpers import validate_proxies, ProxyManager
                
                # Load proxies first
                temp_manager = ProxyManager(args.proxy_file)
                all_proxies = temp_manager.proxies
                print(f"{C}[*] Testing {len(all_proxies)} proxies...{X}")
                
                # Validate them
                working_proxies = validate_proxies(all_proxies)
                
                if not working_proxies:
                    print(f"{R}[✘] No working proxies found{X}")
                    sys.exit(1)
                
                print(f"{G}[+] Found {len(working_proxies)} working proxies out of {len(all_proxies)}{X}")
                
                # Save working proxies to temp file
                temp_proxy_file = "validated_proxies.txt"
                with open(temp_proxy_file, 'w', encoding='utf-8') as f:
                    for proxy in working_proxies:
                        f.write(proxy + '\n')
                
                set_proxy_manager(temp_proxy_file)
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
            with open(args.email_file, 'r', encoding='utf-8') as f:
                emails = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            # Validate email formats
            valid_emails = []
            for email in emails:
                if re.findall(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                    valid_emails.append(email)
                else:
                    print(f"{Y}[!] Skipping invalid email format: {email}{X}")
            
            if not valid_emails:
                print(f"{R}[✘] Error: No valid emails found in {args.email_file}{X}")
                sys.exit(1)
            
            print(f"{C}[+] Loaded {len(valid_emails)} {'email' if len(valid_emails) == 1 else 'emails'} from {args.email_file}{X}")
            is_email = True
            targets = valid_emails
        except FileNotFoundError:
            print(f"{R}[✘] Error: File not found: {args.email_file}{X}")
            sys.exit(1)
        except Exception as e:
            print(f"{R}[✘] Error reading email file: {e}{X}")
            sys.exit(1)
    # Handle bulk username file
    elif args.username_file:
        try:
            with open(args.username_file, 'r', encoding='utf-8') as f:
                usernames = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if not usernames:
                print(f"{R}[✘] Error: No valid usernames found in {args.username_file}{X}")
                sys.exit(1)
            print(f"{C}[+] Loaded {len(usernames)} {'username' if len(usernames) == 1 else 'usernames'} from {args.username_file}{X}")
            is_email = False
            targets = usernames
        except FileNotFoundError:
            print(f"{R}[✘] Error: File not found: {args.username_file}{X}")
            sys.exit(1)
        except Exception as e:
            print(f"{R}[✘] Error reading username file: {e}{X}")
            sys.exit(1)
    else:
        is_email = args.email is not None
        if is_email and not re.findall(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", args.email):
            print(R + "[✘] Error: Invalid email format." + X)
            sys.exit(1)

        target_name = args.username or args.email
        targets = [target_name]

    # Handle permutations (only for single username/email)
    if args.permute and not (args.username_file or args.email_file):
        target_name = args.username or args.email
        targets = generate_permutations(
            target_name, args.permute, args.stop, is_email)
        print(
            C + f"[+] Generated {len(targets)} permutations" + Style.RESET_ALL)
    elif args.permute and (args.username_file or args.email_file):
        print(f"{R}[✘] Error: Permutations not supported with file-based scanning{X}")
        sys.exit(1)

    results = []

    for i, target in enumerate(targets):
        if i != 0 and args.delay:
            time.sleep(args.delay)

        if is_email:
            print(f"\n{Fore.CYAN} Checking email: {target}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.CYAN} Checking username: {target}{Style.RESET_ALL}")

        if args.module:
            modules = find_module(args.module, is_email)
            fn = run_email_module_batch if is_email else run_user_module
            if modules:
                for module in modules:
                    results.extend(fn(module, target))
            else:
                print(
                    R +
                    f"[!] {'Email' if is_email else 'User'} module '{args.module}' not found." +
                    Style.RESET_ALL
                )
        
        elif args.category:
            cat_path = load_categories(is_email).get(args.category)
            fn = run_email_category_batch if is_email else run_user_category
            if cat_path:
                results.extend(fn(cat_path, target))
            else:
                print(
                    R +
                    f"[!] {'Email' if is_email else 'User'} category '{args.module}' not found." +
                    Style.RESET_ALL
                )
        else:
            fn = run_email_full_batch if is_email else run_user_full
            results.extend(fn(target))

    if args.output:
        content = formatter.into_csv(
            results) if args.format == "csv" else formatter.into_json(results)
        with open(args.output, "a", encoding="utf-8") as f:
            f.write(content)
        print(G + f"\n[+] Results saved to {args.output}" + Style.RESET_ALL)


if __name__ == "__main__":
    main()
