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


def run_checks(username):

    from user_scanner import tech, social, community

    categories = [
        ("TECH", tech),
        ("SOCIAL", social),
        ("COMMUNITY", community)
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
