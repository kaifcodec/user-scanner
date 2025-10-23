import argparse
from user_scanner.core.orchestrator import run_checks, load_modules
from colorama import Fore, Style

CATEGORY_MAPPING = {
    "dev": "dev",
    "social": "social",
    "creator": "creator",
    "community": "community"
}

def list_modules(category=None):
    from user_scanner import dev, social, creator, community
    packages = {
        "dev": dev,
        "social": social,
        "creator": creator,
        "community": community
    }

    categories_to_list = [category] if category else packages.keys()

    for cat_name in categories_to_list:
        package = packages[cat_name]
        modules = load_modules(package)
        print(Fore.MAGENTA + f"\n== {cat_name.upper()} SITES =={Style.RESET_ALL}")
        for module in modules:
            site_name = module.__name__.split(".")[-1]
            print(f"  - {site_name}")

def main():
    parser = argparse.ArgumentParser(
        prog="user-scanner",
        description="Scan usernames across multiple platforms."
    )
    parser.add_argument(
        "-u", "--username", help="Username to scan across platforms"
    )
    parser.add_argument(
        "-c", "--category", choices=CATEGORY_MAPPING.keys(),
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

    args = parser.parse_args()

    if args.list:
        list_modules(args.category)
        return

    if not args.username:
        print(Fore.RED + "[!] Please provide a username with -u or --username." + Style.RESET_ALL)
        return

    from user_scanner import dev, social, creator, community

    if args.module:
        # Single module search across all categories
        packages = [dev, social, creator, community]
        found = False
        for package in packages:
            modules = load_modules(package)
            for module in modules:
                site_name = module.__name__.split(".")[-1]
                if site_name.lower() == args.module.lower():
                    from user_scanner.core.orchestrator import run_module_single
                    run_module_single(module, args.username)
                    found = True
        if not found:
            print(Fore.RED + f"[!] Module '{args.module}' not found in any category." + Style.RESET_ALL)
    elif args.category:
        # Category-wise scan
        category_package = eval(CATEGORY_MAPPING[args.category])
        from user_scanner.core.orchestrator import run_checks_category
        run_checks_category(category_package, args.username, args.verbose)
    else:
        # Full scan
        run_checks(args.username)

if __name__ == "__main__":
    main()
