import asyncio
import inspect
import concurrent.futures
from pathlib import Path
from types import ModuleType
from typing import Callable, List, Dict, Optional, Set
import threading

import httpx
from colorama import Fore, Style

from user_scanner.core.helpers import (
    ScanConfig,
    find_category,
    get_proxy,
    get_scan_func,
    get_site_name,
    is_loud,
    load_categories,
    load_modules,
)
from user_scanner.core.result import Result


MAX_CONCURRENT_REQUESTS = 60
_shared_executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS)

async def _async_worker(
    module: ModuleType,
    username: str,
    sem: asyncio.Semaphore,
    configs: ScanConfig,
    printed_cats: Optional[Set] = None,
    cat_override: Optional[str] = None
) -> Result:
    async with sem:
        site_name = get_site_name(module)
        func = get_scan_func(module)
        actual_cat = cat_override or find_category(module) or "Unknown"

        params = {
            "site_name": site_name.capitalize(),
            "username": username,
            "category": actual_cat,
        }

        if not func:
            return Result.error(f"{site_name} has no validate_ function", **params).show(configs)

        if not configs.allow_loud and is_loud(site_name):
            return Result.skipped().update(**params).show(configs)

        try:
            if inspect.iscoroutinefunction(func):
                result = await func(username)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(_shared_executor, func, username)
        except Exception as e:
            result = Result.error(e)

        return result.update(**params)


async def _run_batch(
    modules: List[ModuleType],
    username: str,
    configs: ScanConfig,
    printed_cats: Optional[Set] = None,
    cat_override: Optional[str] = None,
    sem: Optional[asyncio.Semaphore] = None
) -> List[Result]:
    if sem is None:
        sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
    tasks = []
    for module in modules:
        tasks.append(
            asyncio.create_task(
                _async_worker(module, username, sem, configs, cat_override=cat_override)
            )
        )

    results = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
        
        actual_cat = result.category or "Unknown"
        if configs.only_found and result.is_found():
            if printed_cats is not None and actual_cat not in printed_cats:
                print(f"\n{Fore.MAGENTA}== {actual_cat.upper()} SITES =={Style.RESET_ALL}")
                printed_cats.add(actual_cat)
                
        result.show(configs)
        results.append(result)
        
    return results


def run_user_module(
    module: ModuleType, username: str, configs: ScanConfig
) -> List[Result]:
    return asyncio.run(_run_batch([module], username, configs))


def run_user_category(
    category_path: Path, username: str, configs: ScanConfig
) -> List[Result]:
    category_name = category_path.stem.capitalize()
    modules = load_modules(category_path)
    printed_cats = set()

    if not configs.only_found:
        print(f"\n{Fore.MAGENTA}== {category_name.upper()} SITES =={Style.RESET_ALL}")
        printed_cats.add(category_name)

    return asyncio.run(
        _run_batch(
            modules,
            username,
            configs,
            printed_cats=printed_cats,
        )
    )


async def _run_user_full_async(username: str, configs: ScanConfig) -> List[Result]:
    categories = list(load_categories(no_nsfw=configs.no_nsfw).items())
    all_results = []
    printed_cats = set()

    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    # 1. Pre-spawn all tasks for all categories (global concurrency)
    category_tasks = []
    for cat_name, cat_path in categories:
        display_name = cat_name.capitalize()
        modules = load_modules(cat_path)
        tasks = []
        for module in modules:
            tasks.append(
                asyncio.create_task(
                    _async_worker(module, username, sem, configs, cat_override=display_name)
                )
            )
        category_tasks.append((display_name, tasks))

    # 2. Await tasks category by category to stream grouped output
    for display_name, tasks in category_tasks:
        if not tasks:
            continue
            
        if not configs.only_found:
            print(f"\n{Fore.MAGENTA}== {display_name.upper()} SITES =={Style.RESET_ALL}")
            printed_cats.add(display_name)
            
        for coro in asyncio.as_completed(tasks):
            result = await coro
            
            if configs.only_found and result.is_found():
                if display_name not in printed_cats:
                    print(f"\n{Fore.MAGENTA}== {display_name.upper()} SITES =={Style.RESET_ALL}")
                    printed_cats.add(display_name)
                    
            result.show(configs)
            all_results.append(result)

    return all_results


def run_user_full(username: str, configs: ScanConfig) -> List[Result]:
    return asyncio.run(_run_user_full_async(username, configs))






_clients: Dict[tuple, httpx.Client] = {}
_clients_lock = threading.Lock()

def get_client(use_http2: bool, proxy_val: Optional[str]) -> httpx.Client:
    key = (use_http2, proxy_val)
    if key not in _clients:
        with _clients_lock:
            if key not in _clients:
                _clients[key] = httpx.Client(http2=use_http2, proxy=proxy_val, verify=True)
    return _clients[key]


def make_request(url: str, **kwargs) -> httpx.Response:
    """Simple wrapper to **httpx.get** that predefines headers and timeout"""
    if "headers" not in kwargs:
        kwargs["headers"] = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "sec-fetch-dest": "document",
        }
    if "show_url" in kwargs:
        kwargs.pop("show_url", None)

    if "timeout" not in kwargs:
        kwargs["timeout"] = 5.0

    if "proxy" not in kwargs:
        proxy_val = get_proxy()
    else:
        proxy_val = kwargs.pop("proxy")

    method = kwargs.pop("method", "GET")
    use_http2 = kwargs.pop("http2", False)

    client = get_client(use_http2, proxy_val)

    max_retries = 0
    for attempt in range(max_retries + 1):
        try:
            return client.request(method.upper(), url, **kwargs)
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            if attempt == max_retries:
                raise e
    raise RuntimeError("Request failed after retries")


def generic_validate(
    url: str, func: Callable[[httpx.Response], Result], **kwargs
) -> Result:
    """
    A generic validate function that makes a request and executes the provided function on the response.
    """
    # Look for 'show_url' in kwargs, if not found, use the request 'url'
    display_url = kwargs.get("show_url", None)

    try:
        response = make_request(url, **kwargs)
        result = func(response)
        # Update the result with the chosen display url
        return result.update(url=display_url)
    except Exception as e:
        return Result.error(e, url=display_url)


def status_validate(
    url: str, available: int | List[int], taken: int | List[int], **kwargs
) -> Result:
    """
    Function that takes a **url** and **kwargs** for the request and
    checks if the request status matches the available or taken.
    **Available** and **Taken** must either be whole numbers or lists of whole numbers.
    """

    def inner(response: httpx.Response):
        # Checks if a number is equal or is contained inside
        def contains(a, b):
            return (isinstance(a, list) and b in a) or (a == b)

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
        return Result.error(f"[{status}] Status didn't match. Report this on Github.")

    # We pass all kwargs (including show_url if it exists) to generic_validate
    return generic_validate(url, inner, **kwargs)
