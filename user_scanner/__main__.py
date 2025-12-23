import argparse
import time
import sys
from user_scanner.cli import printer
from user_scanner.core.orchestrator import generate_permutations, load_categories
from colorama import Fore, Style
from user_scanner.cli.banner import print_banner
from typing import List
from user_scanner.core.result import Result
from user_scanner.core.helpers import is_last_value
from user_scanner.utils.updater_logic import check_for_updates
from user_scanner.utils.update import update_self

# Color configs
R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN
Y = Fore.YELLOW
X = Fore.RESET


MAX_PERMUTATIONS_LIMIT = 100 # To prevent excessive generation


def main():

    parser = argparse.ArgumentParser(
        prog="user-scanner",
        description="Scan usernames across multiple platforms."
    )
    parser.add_argument(
        "-u", "--username",  help="Username to scan across platforms"
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
        "-p", "--permute",type=str,help="Generate username permutations using a string pattern (e.g -p 234)"
    )
    parser.add_argument(
        "-s", "--stop",type=int,default=MAX_PERMUTATIONS_LIMIT,help="Limit the number of username permutations generated"
    )

    parser.add_argument(
        "-d", "--delay",type=float,default=0,help="Delay in seconds between requests (recommended: 1-2 seconds)"
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

    args = parser.parse_args()

    Printer = printer.Printer(args.format)

    if args.update is True:
        update_self()
        print(f"[{G}+{X}] {G}Update successful. Please restart the tool.{X}")
        sys.exit(0)

    if args.list:
        Printer.print_modules(args.category)
        return

    check_for_updates()

    if not args.username:
        parser.print_help()
        return


    if Printer.is_console:
        print_banner()

    if args.permute and args.delay == 0 and Printer.is_console:
        print(
        Y
        + "[!] Warning: You're generating multiple usernames with NO delay between requests. "
        "This may trigger rate limits or IP bans. Use --delay 1 or higher. (Use only if the sites throw errors otherwise ignore)\n"
        + Style.RESET_ALL)

    usernames = [args.username]  # Default single username list

    # Added permutation support , generate all possible permutation of given sequence.
    if args.permute:
        usernames = generate_permutations(args.username, args.permute , args.stop)
        if Printer.is_console:
            print(
                C + f"[+] Generated {len(usernames)} username permutations" + Style.RESET_ALL)

    if args.module and "." in args.module:
        args.module = args.module.replace(".", "_")

    def run_all_usernames(func, arg = None) -> List[Result]:
        """
        Executes a function for all given usernames.
        Made in order to simplify main()
        """
        results = []
        print(Printer.get_start())
        for i, name in enumerate(usernames):
            is_last = i == len(usernames) - 1
            if arg is None:
                results.extend(func(name, Printer, is_last))
            else:
                results.extend(func(arg, name, Printer, is_last))
            if args.delay > 0 and not is_last:
                time.sleep(args.delay)
        if Printer.is_json:
            print(Printer.get_end())
        return results

    results =  []

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

    if args.output and Printer.is_console:
        msg = (
            "\n[!] The console format cannot be "
            f"written to file: '{args.output}'."
        )
        print(R + msg + Style.RESET_ALL)
        return

    content = Printer.get_start()

    for i,result in enumerate(results):
        char = "" if Printer.is_csv or is_last_value(results, i) else ","
        content += "\n" + Printer.get_result_output(result) + char

    if Printer.is_json:
        content += "\n" + Printer.get_end()

    with open(args.output, "a", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
