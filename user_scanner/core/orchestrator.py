import importlib
import importlib.util
from colorama import Fore, Style
from concurrent.futures import ThreadPoolExecutor
from itertools import permutations
import httpx
from pathlib import Path
from user_scanner.cli.printer import Printer
from user_scanner.core.result import Result, AnyResult
from typing import Callable, Dict, List
from user_scanner.core.utils import get_site_name, is_last_value


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


def find_module(name: str):
    name = name.lower()

    matches = [
        module
        for category_path in load_categories().values()
        for module in load_modules(category_path)
        if module.__name__.split(".")[-1].lower() == name
    ]

    return matches


def worker_single(module, username: str) -> Result:
    func = next((getattr(module, f) for f in dir(module)
                 if f.startswith("validate_") and callable(getattr(module, f))), None)

    site_name = get_site_name(module)

    if not func:
        return Result.error(f"{site_name} has no validate_ function")

    try:
        return func(username)
    except Exception as e:
        return Result.error(e)


def run_module_single(module, username: str, printer: Printer, last: bool = True) -> Result:
    # Just executes as if it was a thread
    result = worker_single(module, username)

    site_name = get_site_name(module)
    msg = printer.get_result_output(
        site_name, username, result
    )
    if last == False and printer.is_json:
        msg += ","
    print(msg)

    return result


def run_checks_category(category_path: Path, username: str, printer: Printer, last: bool = True) -> List[Result]:
    modules = load_modules(category_path)

    if printer.is_console:
        category_name = category_path.stem.capitalize()
        print(f"\n{Fore.MAGENTA}== {category_name} SITES =={Style.RESET_ALL}")

    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        exec_map = executor.map(lambda m: worker_single(m, username), modules)
        for i, result in enumerate(exec_map):
            results.append(result)

            is_last = last and is_last_value(modules, i)
            site_name = get_site_name(modules[i])
            msg = printer.get_result_output(
                site_name, username, result
            )
            if is_last == False and printer.is_json:
                msg += ","
            print(msg)

    return results


def run_checks(username: str, printer: Printer, last: bool = True) -> List[Result]:
    if printer.is_console:
        print(f"\n{Fore.CYAN} Checking username: {username}{Style.RESET_ALL}")

    results = []

    categories = list(load_categories().values())
    for i, category_path in enumerate(categories):
        last_cat: int = last and (i == len(categories) - 1)
        temp = run_checks_category(category_path, username, printer, last_cat)
        results.extend(temp)

    return results


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
