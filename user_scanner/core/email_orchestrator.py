import asyncio
from pathlib import Path
from types import ModuleType
from typing import List, Optional, Set

from colorama import Fore, Style

from user_scanner.core.helpers import (
    ScanConfig,
    find_category,
    load_categories,
    load_modules,
)
from user_scanner.core.result import Result, Status

# Concurrency control
MAX_CONCURRENT_REQUESTS = 25


async def _async_worker(
    module: ModuleType,
    email: str,
    sem: asyncio.Semaphore,
    configs: ScanConfig,
    printed_cats: Optional[Set] = None,
) -> Result:
    async with sem:
        module_name = module.__name__.split(".")[-1]
        func_name = f"validate_{module_name}"
        actual_cat = find_category(module) or "Email"

        params = {
            "site_name": module_name.capitalize(),
            "username": email,
            "category": actual_cat,
            "is_email": True,
        }

        if not hasattr(module, func_name):
            return (
                Result.error(f"Function {func_name} not found")
                .update(**params)
                .show(configs)
            )

        func = getattr(module, func_name)

        try:
            res = func(email)
            result = await res if asyncio.iscoroutine(res) else res
        except Exception as e:
            result = Result.error(e)

        result.update(**params)

        # Logic to print header dynamically for --only-found streaming
        if configs.only_found and result.status == Status.TAKEN:
            if printed_cats is not None and actual_cat not in printed_cats:
                print(
                    f"\n{Fore.MAGENTA}== {actual_cat.upper()} SITES =={Style.RESET_ALL}"
                )
                printed_cats.add(actual_cat)

        return result.show(configs)


async def _run_batch(
    modules: List[ModuleType],
    email: str,
    configs: ScanConfig,
    printed_cats: Optional[Set] = None,
) -> List[Result]:
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = []
    for module in modules:
        tasks.append(
            _async_worker(
                module,
                email,
                sem,
                configs,
                printed_cats=printed_cats,
            )
        )

    if not tasks:
        return []
    return list(await asyncio.gather(*tasks))


def run_email_module_batch(
    module: ModuleType, email: str, configs: ScanConfig
) -> List[Result]:
    return asyncio.run(_run_batch([module], email, configs))


def run_email_category_batch(
    category_path: Path, email: str, configs: ScanConfig
) -> List[Result]:
    cat_name = category_path.stem.capitalize()
    modules = load_modules(category_path)
    printed_cats = set()

    if not configs.only_found:
        print(f"\n{Fore.MAGENTA}== {cat_name.upper()} SITES =={Style.RESET_ALL}")
        printed_cats.add(cat_name)

    return asyncio.run(
        _run_batch(
            modules,
            email,
            configs,
            printed_cats=printed_cats,
        )
    )


def run_email_full_batch(email: str, configs: ScanConfig) -> List[Result]:
    categories = load_categories(is_email=True)
    all_results = []
    printed_cats = set()

    for cat_name, cat_path in categories.items():
        modules = load_modules(cat_path)

        if not configs.only_found:
            print(f"\n{Fore.MAGENTA}== {cat_name.upper()} SITES =={Style.RESET_ALL}")
            printed_cats.add(cat_name)

        cat_results = asyncio.run(
            _run_batch(
                modules,
                email,
                configs,
                printed_cats=printed_cats,
            )
        )
        all_results.extend(cat_results)

    return all_results
