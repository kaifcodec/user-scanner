import argparse
import time
import sys
import re
from user_scanner.core.orchestrator import generate_permutations, load_categories, load_modules
from colorama import Fore, Style
from user_scanner.cli.banner import print_banner
from typing import List
from user_scanner.core.result import Result
from user_scanner.core.version import load_local_version
from user_scanner.core.helpers import is_last_value
from user_scanner.core import formatter
from user_scanner.utils.updater_logic import check_for_updates
from user_scanner.utils.update import update_self

# Color configs
R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN
Y = Fore.YELLOW
X = Fore.RESET


MAX_PERMUTATIONS_LIMIT = 100  # To prevent excessive generation


def main():

    parser = argparse.ArgumentParser(
        prog="user-scanner",
        description="Scan usernames across multiple platforms."
    )

    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument(
        "-u", "--username",  help="Username to scan across platforms"
    )
    group.add_argument(
        "-e", "--email",  help="Email to scan across platforms"
    )
    parser.add_argument(
        "-c", "--category", choices=load_categories().keys(),
        help="Scan all platforms in a category"
    )
    parser.add_argument(
        "-m", "--module", help="Scan a single specific module across all categories"
    )
    parser.add_argument(
        "-l", "--list", action="store_true", help="List all available modules by category"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "-p", "--permute", type=str, help="Generate username permutations using a string pattern (e.g -p 234)"
    )
    parser.add_argument(
        "-s", "--stop", type=int, default=MAX_PERMUTATIONS_LIMIT, help="Limit the number of username permutations generated"
    )
    parser.add_argument(
        "-d", "--delay", type=float, default=0, help="Delay in seconds between requests (recommended: 1-2 seconds)"
    )
    parser.add_argument(
        "-f", "--format", choices=["console", "csv", "json"], default="console", help="Specify the output format (default: console)"
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Specify the output file"
    )
    parser.add_argument(
        "-U", "--update", action="store_true",  help="Update user-scanner to latest version"
    )
    parser.add_argument(
        "--version", action="store_true", help="Print the current pypi version of the tool"
    )
    args = parser.parse_args()

    if args.update is True:
        update_self()
        print(f"[{G}+{X}] {G}Update successful. Please restart the tool.{X}")
        sys.exit(0)

    if args.list:
        categories = load_categories()
        for cat_name, cat_path in categories.items():
            modules = load_modules(cat_path)
            print(Fore.MAGENTA +
                  f"\n== {cat_name.upper()} SITES =={Style.RESET_ALL}")
            for module in modules:
                site_name = module.__name__.split(".")[-1].capitalize()
                print(f"  - {site_name}")

        return

    if args.version:
        version, _ = load_local_version()
        print(f"user-scanner current version -> {G}{version}{X}")
        sys.exit(0)
    check_for_updates()

    if not (args.username or args.email):
        parser.print_help()
        return

    print_banner()

    is_email = args.email is not None
    if is_email and not re.findall(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", args.email):
        print(R + "[✘] Error: Invalid email." + X)
        sys.exit(1)

    if args.permute and args.delay == 0:
        print(
            Y
            + "[!] Warning: You're generating multiple usernames with NO delay between requests. "
            "This may trigger rate limits or IP bans. Use --delay 1 or higher. (Use only if the sites throw errors otherwise ignore)\n"
            + Style.RESET_ALL)

    name = args.username or args.email  # Username or email
    usernames = [name]  # Default single username list

    # Added permutation support , generate all possible permutation of given sequence.
    if args.permute:
        usernames = generate_permutations(
            name, args.permute, args.stop, is_email)
        print(
            C + f"[+] Generated {len(usernames)} username permutations" + Style.RESET_ALL)

    if args.module and "." in args.module:
        args.module = args.module.replace(".", "_")

    def run_all_usernames(func, arg=None) -> List[Result]:
        """
        Executes a function for all given usernames.
        Made in order to simplify main()
        """
        results = []
        for i, name in enumerate(usernames):
            is_last = is_last_value(usernames, i)
            if arg is None:
                results.extend(func(name))
            else:
                results.extend(func(arg, name))
            if args.delay > 0 and not is_last:
                time.sleep(args.delay)
        return results

    results = []

    if args.module:
        # Single module search across all categories
        from user_scanner.core.orchestrator import run_module_single, find_module
        modules = find_module(args.module)

        if len(modules) > 0:
            for module in modules:
                results.extend(run_all_usernames(run_module_single, module))
        else:
            print(
                R + f"[!] Module '{args.module}' not found in any category." + Style.RESET_ALL)

    elif args.category:
        # Category-wise scan
        category_package = load_categories().get(args.category)
        from user_scanner.core.orchestrator import run_checks_category
        results = run_all_usernames(run_checks_category, category_package)

    else:
        # Full scan
        from user_scanner.core.orchestrator import run_checks
        results = run_all_usernames(run_checks)

    if not args.output:
        return

    if args.output and args.format == "console":
        msg = (
            "\n[!] The console format cannot be "
            f"written to file: '{args.output}'."
        )
        print(R + msg + Style.RESET_ALL)
        return

        
    content = formatter.into_csv(results) if args.format == "csv" else formatter.into_json(results)

    with open(args.output, "a", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
