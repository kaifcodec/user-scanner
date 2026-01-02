import argparse
import time
import sys
import re
from colorama import Fore, Style
from typing import List

from user_scanner.cli.banner import print_banner
from user_scanner.core.result import Result
from user_scanner.core.version import load_local_version
from user_scanner.core import formatter
from user_scanner.utils.updater_logic import check_for_updates
from user_scanner.utils.update import update_self

from user_scanner.core.helpers import (
    load_categories,
    load_modules,
    find_module,
    is_last_value,
    get_site_name
)

from user_scanner.core.orchestrator import (
    generate_permutations,
    run_checks,
    run_checks_category,
    run_module_single
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

    if is_email:
        if args.module:
            modules = find_module(args.module, is_email=True)
            if modules:
                for module in modules:
                    results.extend(run_email_module_batch(module, targets))
            else:
                print(
                    R + f"[!] Email module '{args.module}' not found." + Style.RESET_ALL)
        elif args.category:
            cat_path = load_categories(is_email=True).get(args.category)
            if cat_path:
                results.extend(run_email_category_batch(cat_path, targets))
            else:
                print(
                    R + f"[!] Email category '{args.category}' not found." + Style.RESET_ALL)
        else:
            results = run_email_full_batch(targets)
    else:
        def run_all_targets(func, arg=None) -> List[Result]:
            all_results = []
            for i, name in enumerate(targets):
                is_last = is_last_value(targets, i)
                res = func(name) if arg is None else func(arg, name)
                if isinstance(res, list):
                    all_results.extend(res)
                else:
                    all_results.append(res)
                if args.delay > 0 and not is_last:
                    time.sleep(args.delay)
            return all_results

        if args.module:
            modules = find_module(args.module, is_email=False)
            if modules:
                for mod in modules:
                    results.extend(run_all_targets(run_module_single, mod))
            else:
                print(
                    R + f"[!] Module '{args.module}' not found." + Style.RESET_ALL)
        elif args.category:
            cat_path = load_categories(is_email=False).get(args.category)
            if cat_path:
                results.extend(run_all_targets(run_checks_category, cat_path))
            else:
                print(
                    R + f"[!] Category '{args.category}' not found." + Style.RESET_ALL)
        else:
            results = run_all_targets(run_checks)

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
