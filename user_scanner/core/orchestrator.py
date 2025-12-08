import importlib
from colorama import Fore, Style
import threading
from itertools import permutations
import httpx
from pathlib import Path
from user_scanner.core.result import Result, AnyResult
from typing import Callable, Dict, List

lock = threading.Condition()
# Basically which thread is the one to print
print_queue = 0


def load_modules(category_path: Path):
    modules = []
    for file in category_path.glob("*.py"):
        if file.name == "__init__.py":
            continue
        spec = importlib.util.spec_from_file_location(file.stem, str(file))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        modules.append(module)
    return modules


def load_categories() -> Dict[str, Path]:
    root = Path(__file__).resolve().parent.parent  # Should be user_scanner
    categories = {}

    for subfolder in root.iterdir():
        if subfolder.is_dir() and \
                not subfolder.name.lower() in ["cli", "utils", "core"] and \
                not "__" in subfolder.name:  # Removes __pycache__
            categories[subfolder.name] = subfolder.resolve()

    return categories


def worker_single(module, username, i):
    global print_queue

    func = next((getattr(module, f) for f in dir(module)
                 if f.startswith("validate_") and callable(getattr(module, f))), None)
    site_name = module.__name__.split('.')[-1].capitalize().replace("_", ".")
    if site_name == "X":
        site_name = "X (Twitter)"

    output = ""
    if func:
        try:
            result = func(username)
            reason = ""

            if isinstance(result, Result) and result.has_reason():
                reason = f" ({result.get_reason()})"

            if result == 1:
                output = f"  {Fore.GREEN}[✔] {site_name} ({username}): Available{Style.RESET_ALL}"
            elif result == 0:
                output = f"  {Fore.RED}[✘] {site_name} ({username}): Taken{Style.RESET_ALL}"
            else:
                output = f"  {Fore.YELLOW}[!] {site_name} ({username}): Error{reason}{Style.RESET_ALL}"
        except Exception as e:
            output = f"  {Fore.YELLOW}[!] {site_name}: Exception - {e}{Style.RESET_ALL}"
    else:
        output = f"  {Fore.YELLOW}[!] {site_name} has no validate_ function{Style.RESET_ALL}"

    with lock:
        # Waits for in-order printing
        while i != print_queue:
            lock.wait()

        print(output)
        print_queue += 1
        lock.notify_all()


def run_module_single(module, username):
    # Just executes as if it was a thread
    worker_single(module, username, print_queue)


def run_checks_category(category_path:Path, username:str, verbose=False):
    global print_queue

    modules = load_modules(category_path)
    category_name = category_path.stem.capitalize()
    print(f"{Fore.MAGENTA}== {category_name} SITES =={Style.RESET_ALL}")

    print_queue = 0

    threads = []
    for i, module in enumerate(modules):
        t = threading.Thread(target=worker_single, args=(module, username, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


def run_checks(username):
    print(f"\n{Fore.CYAN} Checking username: {username}{Style.RESET_ALL}\n")

    for category_path in load_categories().values():
        run_checks_category(category_path, username)
        print()


def make_get_request(url: str, **kwargs) -> httpx.Response:
    """Simple wrapper to **httpx.get** that predefines headers and timeout"""
    if not "headers" in kwargs:
        kwargs["headers"] = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "en-US,en;q=0.9",
            'sec-fetch-dest': "document",
        }

    if not "timeout" in kwargs:
        kwargs["timeout"] = 5.0

    return httpx.get(url, **kwargs)


def generic_validate(url: str, func: Callable[[httpx.Response], AnyResult], **kwargs) -> AnyResult:
    """
    A generic validate function that makes a request and executes the provided function on the response.
    """
    try:
        response = make_get_request(url, **kwargs)
        return func(response)
    except Exception as e:
        return Result.error(e)


def status_validate(url: str, available: int | List[int], taken: int | List[int], **kwargs) -> Result:
    """
    Function that takes a **url** and **kwargs** for the request and 
    checks if the request status matches the availabe or taken.
    **Available** and **Taken** must either be whole numbers or lists of whole numbers.
    """
    def inner(response: httpx.Response):
        # Checks if a number is equal or is contained inside
        def contains(a, b): return (isinstance(a, list) and b in a) or (a == b)
        status = response.status_code
        available_value = contains(available, status)
        taken_value = contains(taken, status)

        if available_value and taken_value:
            # Can't be both available and taken
            return Result.error("Invalid status match. Report this on Github.")
        elif available_value:
            return Result.available()
        elif taken_value:
            return Result.taken()
        return Result.error("Status didn't match. Report this on Github.")

    return generic_validate(url, inner, **kwargs)

def generate_permutations(username, pattern, limit=None):
    """
    Generate all order-based permutations of characters in `pattern`
    appended after `username`.
    """
    permutations_set = {username}

    chars = list(pattern)

    # generate permutations of length 1 → len(chars)
    for r in range(1, len(chars) + 1):
        for combo in permutations(chars, r):
            permutations_set.add(username + ''.join(combo))
            if limit and len(permutations_set) >= limit:
                return list(permutations_set)[:limit]

    return sorted(permutations_set)
