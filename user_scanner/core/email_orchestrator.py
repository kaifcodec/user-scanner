import asyncio
from pathlib import Path
from typing import List
from types import ModuleType

from user_scanner.core.helpers import load_categories, load_modules, find_category
from user_scanner.core.result import Result


MAX_CONCURRENT_REQUESTS = 15


async def _async_worker(module: ModuleType, email: str, sem: asyncio.Semaphore) -> Result:
    async with sem:
        module_name = module.__name__.split(".")[-1]
        func_name = f"validate_{module_name}"

        if not hasattr(module, func_name):
            return Result.error(f"Function {func_name} not found")

        func = getattr(module, func_name)

        try:
            res = func(email)
            result = await res if asyncio.iscoroutine(res) else res
        except Exception as e:
            result = Result.error(e)

        cat_name = find_category(module)
        result.update(
            site_name=module_name.capitalize(),
            username=email,
            category=cat_name,
            is_email=True,
        )

        print(result.get_console_output())
        return result


async def _run_batch(modules: List[ModuleType], emails: List[str]) -> List[Result]:
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = []

    for module in modules:
        for email in emails:
            tasks.append(_async_worker(module, email, sem))

    if not tasks:
        return []

    return list(await asyncio.gather(*tasks))


def run_email_module_batch(module: ModuleType, emails: List[str]) -> List[Result]:
    return asyncio.run(_run_batch([module], emails))


def run_email_category_batch(category_path: Path, emails: List[str]) -> List[Result]:
    modules = load_modules(category_path)
    return asyncio.run(_run_batch(modules, emails))


def run_email_full_batch(emails: List[str]) -> List[Result]:
    categories = load_categories(is_email=True)
    all_results = []

    for cat_path in categories.values():
        modules = load_modules(cat_path)
        cat_results = asyncio.run(_run_batch(modules, emails))
        all_results.extend(cat_results)

    return all_results
