import asyncio
import inspect
from typing import List
from types import ModuleType

from user_scanner.core.result import Result
from user_scanner.core.helpers import find_category, get_site_name, load_modules, load_categories


async def check(module: ModuleType, target: str) -> Result:
    module_name = module.__name__.split(".")[-1]
    func_name = f"validate_{module_name}"

    module_path = getattr(module, "__file__", "")
    is_email = "email_scan" in module_path

    site_label = get_site_name(module)
    category = find_category(module) or ("Email" if is_email else "Username")

    func = getattr(module, func_name, None)
    if not func:
        return Result.error(f"Function {func_name} not found").update(
            site_name=site_label, username=target, category=category, is_email=is_email
        )

    try:
        if inspect.iscoroutinefunction(func):
            result = await func(target)
        else:
            result = func(target)
    except Exception as e:
        result = Result.error(e)

    return result.update(
        site_name=site_label,
        username=target,
        category=category,
        is_email=is_email
    )


async def check_category(category_name: str, target: str, is_email: bool = True) -> List[Result]:
    categories = load_categories(is_email=is_email)
    cat_path = next((p for name, p in categories.items()
                    if name.lower() == category_name.lower()), None)

    if not cat_path:
        mode = "email_scan" if is_email else "user_scan"
        raise ValueError(f"Category '{category_name}' not found in {mode}")

    modules = load_modules(cat_path)
    tasks = [check(m, target) for m in modules]
    return list(await asyncio.gather(*tasks))


async def check_all(target: str, is_email: bool = True) -> List[Result]:
    categories = load_categories(is_email=is_email)
    results = []

    all_tasks = [check_category(cat_name, target, is_email)
                 for cat_name in categories.keys()]
    nested_results = await asyncio.gather(*all_tasks)

    for sublist in nested_results:
        results.extend(sublist)

    return results
