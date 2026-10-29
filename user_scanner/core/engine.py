import asyncio
import inspect
import concurrent.futures

from typing import List
from types import ModuleType
from user_scanner.core.result import Result
from user_scanner.core.helpers import (
    ScanConfig,
    find_category,
    get_site_name,
    is_loud,
    load_categories,
    load_modules,
)

_shared_executor = concurrent.futures.ThreadPoolExecutor(max_workers=60)


def _categories(is_email: bool, configs: ScanConfig):
    if configs.no_nsfw:
        return load_categories(is_email=is_email, no_nsfw=True)
    return load_categories(is_email=is_email)


def _blocked(configs: ScanConfig, site_label: str, category: str, is_email: bool) -> bool:
    if configs.no_nsfw and category.lower() == "adult":
        return True
    return not configs.allow_loud and is_loud(site_label, is_email=is_email)


async def check(module: ModuleType, target: str, configs: ScanConfig | None = None) -> Result:
    configs = configs or ScanConfig()
    module_name = module.__name__.split(".")[-1]
    func_name = f"validate_{module_name}"

    module_path = getattr(module, "__file__", "")
    is_email = "email_scan" in module_path

    site_label = get_site_name(module)
    category = find_category(module) or ("Email" if is_email else "Username")
    meta = {
        "site_name": site_label,
        "username": target,
        "category": category,
        "is_email": is_email,
    }

    if _blocked(configs, site_label, category, is_email):
        return Result.skipped().update(**meta)

    func = getattr(module, func_name, None)
    if not func:
        return Result.error(f"Function {func_name} not found").update(**meta)

    try:
        if inspect.iscoroutinefunction(func):
            result = await func(target)
        else:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(_shared_executor, func, target)
    except Exception as e:
        result = Result.error(e)

    return result.update(**meta)


async def check_category(
    category_name: str,
    target: str,
    is_email: bool = True,
    configs: ScanConfig | None = None,
) -> List[Result]:
    categories = _categories(is_email, configs or ScanConfig())
    cat_path = next((p for name, p in categories.items()
                    if name.lower() == category_name.lower()), None)

    if not cat_path:
        mode = "email_scan" if is_email else "user_scan"
        raise ValueError(f"Category '{category_name}' not found in {mode}")

    modules = load_modules(cat_path)
    if configs is None:
        tasks = [check(m, target) for m in modules]
    else:
        tasks = [check(m, target, configs) for m in modules]
    return list(await asyncio.gather(*tasks))


async def check_all(
    target: str, is_email: bool = True, configs: ScanConfig | None = None
) -> List[Result]:
    categories = _categories(is_email, configs or ScanConfig())
    results = []

    if configs is None:
        all_tasks = [check_category(cat_name, target, is_email) for cat_name in categories.keys()]
    else:
        all_tasks = [
            check_category(cat_name, target, is_email, configs) for cat_name in categories.keys()
        ]
    nested_results = await asyncio.gather(*all_tasks)

    for sublist in nested_results:
        results.extend(sublist)

    return results

