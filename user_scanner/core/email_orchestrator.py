import asyncio
from pathlib import Path
from types import ModuleType
from typing import List

from colorama import Fore, Style

from user_scanner.core.helpers import find_category, load_categories, load_modules
from user_scanner.core.result import Result

# Concurrency control
MAX_CONCURRENT_REQUESTS = 15


async def _async_worker(module: ModuleType, email: str, sem: asyncio.Semaphore, show_url: bool = False) -> Result:
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
                Result.error(f"Function {func_name} not found").update(**params).show(show_url=show_url)
            )

        func = getattr(module, func_name)

        try:
            res = func(email)
            result = await res if asyncio.iscoroutine(res) else res
        except Exception as e:
            result = Result.error(e)

        return result.update(**params).show(show_url=show_url)


async def _run_batch(modules: List[ModuleType], email: str, show_url: bool = False) -> List[Result]:
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = []
    for module in modules:
        tasks.append(_async_worker(module, email, sem, show_url=show_url))

    if not tasks:
        return []
    return list(await asyncio.gather(*tasks))


def run_email_module_batch(module: ModuleType, email: str, show_url: bool = False) -> List[Result]:
    return asyncio.run(_run_batch([module], email, show_url=show_url))


def run_email_category_batch(category_path: Path, email: str, show_url: bool = False) -> List[Result]:
    cat_name = category_path.stem.capitalize()
    print(f"\n{Fore.MAGENTA}== {cat_name} SITES =={Style.RESET_ALL}")

    modules = load_modules(category_path)
    return asyncio.run(_run_batch(modules, email, show_url=show_url))


def run_email_full_batch(email: str, show_url: bool = False) -> List[Result]:
    categories = load_categories(is_email=True)
    all_results = []

    for cat_name, cat_path in categories.items():
        print(f"\n{Fore.MAGENTA}== {cat_name.upper()} SITES =={Style.RESET_ALL}")

        modules = load_modules(cat_path)
        cat_results = asyncio.run(_run_batch(modules, email, show_url=show_url))
        all_results.extend(cat_results)

    return all_results
