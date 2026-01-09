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
    generate_permutations
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

    parser.add_argument("-c", "--category",
                        help="Scan all platforms in a category")

    parser.add_argument("-m", "--module", help="Scan a single specific module")

    parser.add_argument("-l", "--list", action="store_true",
                        help="List all available modules for username scanning")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output")

    parser.add_argument("-p", "--permute", type=str,
                        help="Generate permutations using a pattern")

    parser.add_argument("-s", "--stop", type=int,
                        default=MAX_PERMUTATIONS_LIMIT, help="Limit permutations")

    parser.add_argument("-d", "--delay", type=float,
                        default=0, help="Delay between requests")

    parser.add_argument(
        "-f", "--format", choices=["console", "csv", "json"], default="console", help="Output format")

    parser.add_argument("-o", "--output", type=str, help="Output file path")

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

    if args.list:
        is_email_list = args.email is not None
        categories = load_categories(is_email_list)
        for cat_name, cat_path in categories.items():
            modules = load_modules(cat_path)
            print(Fore.MAGENTA +
                  f"\n== {cat_name.upper()} SITES =={Style.RESET_ALL}")
            for module in modules:
                print(f"  - {get_site_name(module)}")
        return

    if not (args.username or args.email):
        parser.print_help()
        return

    check_for_updates()
    print_banner()

    is_email = args.email is not None
    if is_email and not re.findall(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", args.email):
        print(R + "[✘] Error: Invalid email format." + X)
        sys.exit(1)

    target_name = args.username or args.email
    targets = [target_name]

    if args.permute:
        targets = generate_permutations(
            target_name, args.permute, args.stop, is_email)
        print(
            C + f"[+] Generated {len(targets)} permutations" + Style.RESET_ALL)

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
        if args.format == "console":
            print(
                R + f"\n[!] Console format cannot be saved to '{args.output}'." + Style.RESET_ALL)
            return

        content = formatter.into_csv(
            results) if args.format == "csv" else formatter.into_json(results)
        with open(args.output, "a", encoding="utf-8") as f:
            f.write(content)
        print(G + f"\n[+] Results saved to {args.output}" + Style.RESET_ALL)


if __name__ == "__main__":
    main()
