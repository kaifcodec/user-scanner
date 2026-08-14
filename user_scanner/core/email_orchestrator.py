import asyncio
import httpx
from pathlib import Path
from types import ModuleType
from typing import List, Optional, Set, Union, Callable

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
    get_global_timeout,
)
from user_scanner.core.result import Result
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

# Monkey-patch httpx clients to automatically use proxies for email scans
_original_async_client_init = httpx.AsyncClient.__init__
_original_client_init = httpx.Client.__init__

def _patched_async_client_init(self, *args, **kwargs):
    if "proxy" not in kwargs and "proxies" not in kwargs:
        proxy = get_proxy()
        if proxy:
            kwargs["proxy"] = proxy
            
    global_timeout = get_global_timeout()
    if global_timeout is not None:
        kwargs["timeout"] = global_timeout
        
    _original_async_client_init(self, *args, **kwargs)

def _patched_client_init(self, *args, **kwargs):
    if "proxy" not in kwargs and "proxies" not in kwargs:
        proxy = get_proxy()
        if proxy:
            kwargs["proxy"] = proxy
            
    global_timeout = get_global_timeout()
    if global_timeout is not None:
        kwargs["timeout"] = global_timeout
        
    _original_client_init(self, *args, **kwargs)

httpx.AsyncClient.__init__ = _patched_async_client_init  # type: ignore[method-assign]
httpx.Client.__init__ = _patched_client_init  # type: ignore[method-assign]


# Concurrency control
MAX_CONCURRENT_REQUESTS = 25

def set_concurrency(val: int):
    global MAX_CONCURRENT_REQUESTS
    MAX_CONCURRENT_REQUESTS = val

async def _async_worker(
    module: ModuleType,
    email: str,
    sem: asyncio.Semaphore,
    configs: ScanConfig,
    printed_cats: Optional[Set] = None,
    on_start: Optional[Callable[[str], None]] = None,
) -> Result:
    async with sem:
        site_name = get_site_name(module)
        if on_start:
            on_start(site_name)
        func = get_scan_func(module)
        actual_cat = find_category(module) or "Email"

        params = {
            "site_name": site_name.capitalize(),
            "username": email,
            "category": actual_cat,
            "is_email": True,
        }

        if not func:
            return Result.error(
                f"{site_name} has no validate_ function", **params
            )

        if not configs.allow_loud and is_loud(site_name, is_email=True):
            return Result.skipped().update(**params)

        try:
            import inspect
            module_timeout = (get_global_timeout() or 15.0) + 10.0
            if inspect.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(email), timeout=module_timeout)
            else:
                result = await asyncio.wait_for(asyncio.to_thread(func, email), timeout=module_timeout)
        except asyncio.TimeoutError:
            result = Result.error(f"Module execution timed out after {module_timeout}s")
        except Exception as e:
            result = Result.error(e)

        return result.update(**params)


async def _run_batch(
    modules: List[ModuleType],
    email: str,
    configs: ScanConfig,
    printed_cats: Optional[Set] = None,
) -> List[Result]:
    if not modules:
        return []

    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
    ) as progress:
        task_id = progress.add_task(f"[cyan]Scanning {email}...", total=len(modules))

        def on_start_cb(site: str):
            progress.update(task_id, description=f"[cyan]Scanning {email}... ({site})")

        tasks = []
        for module in modules:
            t = asyncio.create_task(
                _async_worker(
                    module,
                    email,
                    sem,
                    configs,
                    printed_cats=printed_cats,
                    on_start=on_start_cb,
                )
            )
            t.add_done_callback(lambda t: progress.advance(task_id))
            tasks.append(t)

        for coro in asyncio.as_completed(tasks):
            result = await coro
            actual_cat = result.category or "Unknown"
            if configs.show_all or result.is_visible(configs):
                if printed_cats is not None and actual_cat not in printed_cats:
                    print(
                        f"\n{Fore.MAGENTA}== {actual_cat.upper()} SITES =={Style.RESET_ALL}"
                    )
                    printed_cats.add(actual_cat)

            result.show(configs)
            results.append(result)

    return results


async def _run_email_module_batch_async(
    module: Union[ModuleType, List[ModuleType]], email: str, configs: ScanConfig
) -> List[Result]:
    loop = asyncio.get_running_loop()
    import concurrent.futures
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=250))
    modules = [module] if isinstance(module, ModuleType) else list(module)
    return await _run_batch(modules, email, configs, printed_cats=set())


def run_email_module_batch(
    module: Union[ModuleType, List[ModuleType]], email: str, configs: ScanConfig
) -> List[Result]:
    return asyncio.run(_run_email_module_batch_async(module, email, configs))


async def _run_email_category_batch_async(
    category_path: Path, email: str, configs: ScanConfig
) -> List[Result]:
    loop = asyncio.get_running_loop()
    import concurrent.futures
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=250))
    cat_name = category_path.stem.capitalize()
    modules = load_modules(category_path)
    printed_cats = set()

    if configs.show_all:
        print(f"\n{Fore.MAGENTA}== {cat_name.upper()} SITES =={Style.RESET_ALL}")
        printed_cats.add(cat_name)

    return await _run_batch(
        modules,
        email,
        configs,
        printed_cats=printed_cats,
    )

def run_email_category_batch(
    category_path: Path, email: str, configs: ScanConfig
) -> List[Result]:
    return asyncio.run(_run_email_category_batch_async(category_path, email, configs))


async def _run_email_full_batch_async(email: str, configs: ScanConfig) -> List[Result]:
    loop = asyncio.get_running_loop()
    import concurrent.futures
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=250))
    categories = load_categories(True, configs.no_nsfw)
    all_results = []
    printed_cats: Set[str] = set()

    # 1. Pre-spawn all tasks for all categories (global concurrency)
    category_modules = []
    total_tasks = 0
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    for cat_name, cat_path in categories.items():
        display_name = cat_name.capitalize()
        modules = load_modules(cat_path)
        category_modules.append((display_name, modules))
        total_tasks += len(modules)

    # 2. Await tasks category by category to stream grouped output
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
    ) as progress:
        task_id = progress.add_task(f"[cyan]Scanning {email}...", total=total_tasks)
        
        def on_start_cb(site: str):
            progress.update(task_id, description=f"[cyan]Scanning {email}... ({site})")
            
        spawned_category_tasks = []
        for display_name, modules in category_modules:
            tasks = []
            for module in modules:
                t = asyncio.create_task(
                    _async_worker(
                        module,
                        email,
                        sem,
                        configs,
                        printed_cats=printed_cats,
                        on_start=on_start_cb,
                    )
                )
                t.add_done_callback(lambda t: progress.advance(task_id))
                tasks.append(t)
            spawned_category_tasks.append((display_name, tasks))
                
        for display_name, tasks in spawned_category_tasks:
            if not tasks:
                continue
                
            if configs.show_all:
                print(f"\n{Fore.MAGENTA}== {display_name.upper()} SITES =={Style.RESET_ALL}")
                printed_cats.add(display_name)
                
            for coro in asyncio.as_completed(tasks):
                result = await coro
                if configs.show_all or result.is_visible(configs):
                    display_name = result.category or "Unknown"
                    if display_name not in printed_cats:
                        print(
                            f"\n{Fore.MAGENTA}== {display_name.upper()} SITES =={Style.RESET_ALL}"
                        )
                        printed_cats.add(display_name)

                result.show(configs)
                all_results.append(result)

    return all_results

def run_email_full_batch(email: str, configs: ScanConfig) -> List[Result]:
    return asyncio.run(_run_email_full_batch_async(email, configs))
