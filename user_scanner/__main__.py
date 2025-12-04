import argparse
import time
import re
from user_scanner.core.orchestrator import run_checks, load_modules , generate_permutations, load_categories
from colorama import Fore, Style
from .cli import banner
from .cli.banner import print_banner

MAX_PERMUTATIONS_LIMIT = 100 # To prevent excessive generation

def list_modules(category=None):
    categories = load_categories()
    categories_to_list = [category] if category else categories.keys()

    for cat_name in categories_to_list:
        path = categories[cat_name]
        modules = load_modules(path)
        print(Fore.MAGENTA +
            f"\n== {cat_name.upper()} SITES =={Style.RESET_ALL}")
        for module in modules:
            site_name = module.__name__.split(".")[-1]
            print(f"  - {site_name}")


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
    
    args = parser.parse_args()
        
    if args.list:
        list_modules(args.category)
        return
    
    if not args.username:
        parser.print_help()
        return
        
    # Special username checks before run
    if (args.module == "x" or args.category == "social"):
        if re.search(r"[^a-zA-Z0-9._-]", args.username):
            print(
                Fore.RED + f"[!] Username '{args.username}' contains unsupported special characters. X (Twitter) doesn't support these." + Style.RESET_ALL)
    if (args.module == "bluesky" or args.category == "social"):
        if re.search(r"[^a-zA-Z0-9\.-]", args.username):
            print(
                Fore.RED + f"[!] Username '{args.username}' contains unsupported special characters. Bluesky will throw error. (Supported: only hyphens and digits)" + Style.RESET_ALL + "\n")
    print_banner()

    if args.permute and args.delay == 0:
        print(
        Fore.YELLOW
        + "[!] Warning: You're generating multiple usernames with NO delay between requests. "
        "This may trigger rate limits or IP bans. Use --delay 1 or higher. (Use only if the sites throw errors otherwise ignore)\n"
        + Style.RESET_ALL)
        
    usernames = [args.username]  # Default single username list
    
    #Added permutation support , generate all possible permutation of given sequence.
    if args.permute:
        usernames = generate_permutations(args.username, args.permute , args.stop)
        print(Fore.CYAN + f"[+] Generated {len(usernames)} username permutations" + Style.RESET_ALL)

    
    
    if args.module and "." in args.module:
        args.module = args.module.replace(".", "_")


    if args.module:
        # Single module search across all categories
        found = False
        for cat_path in load_categories().values():
            modules = load_modules(cat_path)
            for module in modules:
                site_name = module.__name__.split(".")[-1]
                if site_name.lower() == args.module.lower():
                    from user_scanner.core.orchestrator import run_module_single
                    for name in usernames:   # <-- permutation support here
                        run_module_single(module, name)
                        if args.delay > 0:
                            time.sleep(args.delay)
                    found = True
        if not found:
            print(
                Fore.RED + f"[!] Module '{args.module}' not found in any category." + Style.RESET_ALL)
    elif args.category:
        # Category-wise scan
        category_package = load_categories().get(args.category)
        from user_scanner.core.orchestrator import run_checks_category
        
        for name in usernames:   # <-- permutation support here
            run_checks_category(category_package, name, args.verbose)
            if args.delay > 0:
                time.sleep(args.delay)
    else:
        # Full scan
        for name in usernames:
            run_checks(name)
            if args.delay > 0:
                time.sleep(args.delay)


if __name__ == "__main__":
    main()
