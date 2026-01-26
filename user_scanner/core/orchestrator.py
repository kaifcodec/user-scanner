from colorama import Fore, Style
from concurrent.futures import ThreadPoolExecutor
import httpx
from pathlib import Path
from user_scanner.core.result import Result
from typing import Callable, List
from types import ModuleType
from user_scanner.core.helpers import find_category,  get_site_name, load_categories, load_modules, get_proxy


def _worker_single(module: ModuleType, username: str) -> Result:
    func = next((getattr(module, f) for f in dir(module)
                 if f.startswith("validate_") and callable(getattr(module, f))), None)

    site_name = get_site_name(module)

    if not func:
        return Result.error(
            f"{site_name} has no validate_ function",
            site_name=site_name,
            username=username,
        )

    try:
        result: Result = func(username)
        result.update(site_name=site_name, username=username)
        return result
    except Exception as e:
        return Result.error(e, site_name=site_name, username=username)
    
def run_user_module(module: ModuleType, username: str) -> List[Result]:
    result = _worker_single(module, username)

    category = find_category(module)
    if category:
        result.update(category=category)

    print(result.get_console_output())

    return [result]


def run_user_category(category_path: Path, username: str) -> List[Result]:
    category_name = category_path.stem.capitalize()
    print(f"\n{Fore.MAGENTA}== {category_name} SITES =={Style.RESET_ALL}")

    results = []
    modules = load_modules(category_path)

    with ThreadPoolExecutor(max_workers=10) as executor:
        exec_map = executor.map(lambda m: _worker_single(m, username), modules)
        for result in exec_map:
            result.update(category=category_name)
            results.append(result)
            result.show()

    return results


def run_user_full(username: str) -> List[Result]:
    results = []

    categories = list(load_categories().values())
    for category_path in categories:
        temp = run_user_category(category_path, username)
        results.extend(temp)

    return results


def make_request(url: str, **kwargs) -> httpx.Response:
    """Simple wrapper to **httpx.get** that predefines headers and timeout"""
    if "headers" not in kwargs:
        kwargs["headers"] = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "en-US,en;q=0.9",
            'sec-fetch-dest': "document",
        }

    if "timeout" not in kwargs:
        kwargs["timeout"] = 5.0

    # Add proxy if available and not already set
    if "proxy" not in kwargs:
        proxy = get_proxy()
        if proxy:
            kwargs["proxy"] = proxy

    method = kwargs.pop("method", "GET")

    return httpx.request(method.upper(), url, **kwargs)


def generic_validate(url: str, func: Callable[[httpx.Response], Result], **kwargs) -> Result:
    """
    A generic validate function that makes a request and executes the provided function on the response.
    """
    try:
        response = make_request(url, **kwargs)
        result = func(response)
        return result
    except Exception as e:
        return Result.error(e, url=url)


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
