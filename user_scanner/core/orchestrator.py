import importlib
import pkgutil
from colorama import Fore, Style

def load_modules(package):

    modules = []
    for _, name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        try:
            module = importlib.import_module(name)
            modules.append(module)
        except Exception as e:
            print(f"Failed to import {name}: {e}")
    return modules

def run_module_single(module, username):

    func = next((getattr(module, f) for f in dir(module)
                 if f.startswith("validate_") and callable(getattr(module, f))), None)
    site_name = module.__name__.split('.')[-1].capitalize()
    if site_name == "X":
        site_name = "X (Twitter)"

    if func:
        try:
            result = func(username)
            if result == 1:
                print(f"  {Fore.GREEN}[✔] {site_name}: Available{Style.RESET_ALL}")
            elif result == 0:
                print(f"  {Fore.RED}[✘] {site_name}: Taken{Style.RESET_ALL}")
            else:
                print(f"  {Fore.YELLOW}[!] {site_name}: Error{Style.RESET_ALL}")
        except Exception as e:
            print(f"  {Fore.YELLOW}[!] {site_name}: Exception - {e}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.YELLOW}[!] {site_name} has no validate_ function{Style.RESET_ALL}")

def run_checks_category(package, username, verbose=False):
    modules = load_modules(package)
    category_name = package.__name__.split('.')[-1].capitalize()
    print(f"{Fore.MAGENTA}== {category_name} SITES =={Style.RESET_ALL}")

    for module in modules:
        run_module_single(module, username)

def run_checks(username):

    from user_scanner import dev, social,creator, community, gaming

    categories = [
        ("DEV", dev),
        ("SOCIAL", social),
        ("CREATOR", creator),
        ("COMMUNITY", community),
        ("GAMING", gaming)
    ]

    print(f"\n{Fore.CYAN} Checking username: {username}{Style.RESET_ALL}\n")

    for cat_name, package in categories:
        try:
            modules = load_modules(package)
        except ModuleNotFoundError:
            continue

        print(f"{Fore.MAGENTA}== {cat_name} SITES =={Style.RESET_ALL}")

        for module in modules:
            # Find the first function starting with "validate_"
            func = None
            for f in dir(module):
                if f.startswith("validate_") and callable(getattr(module, f)):
                    func = getattr(module, f)
                    break
            if not func:
                continue

            site_name = module.__name__.split('.')[-1].capitalize()
            if site_name == "X":
               site_name = "X (Twitter)"
            try:
                result = func(username)
                if result == 1:
                    print(f"  {Fore.GREEN}[✔] {site_name}: Available{Style.RESET_ALL}")
                elif result == 0:
                    print(f"  {Fore.RED}[✘] {site_name}: Taken{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.YELLOW}[!] {site_name}: Error{Style.RESET_ALL}")
            except Exception as e:
                print(f"  {Fore.YELLOW}[!] {site_name}: Exception - {e}{Style.RESET_ALL}")

        print()
