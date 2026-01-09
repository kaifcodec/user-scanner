import importlib
import importlib.util
from itertools import permutations
from types import ModuleType
from pathlib import Path
from typing import Dict, List


def get_site_name(module) -> str:
    name = module.__name__.split('.')[-1].capitalize().replace("_", ".")
    if name == "X":
        return "X (Twitter)"
    return name


def load_modules(category_path: Path) -> List[ModuleType]:
    modules = []
    for file in category_path.glob("*.py"):
        if file.name == "__init__.py":
            continue
        spec = importlib.util.spec_from_file_location(file.stem, str(file))
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        modules.append(module)
    return modules


def load_categories(is_email: bool = False) -> Dict[str, Path]:
    folder_name = "email_scan" if is_email else "user_scan"
    root = Path(__file__).resolve().parent.parent / folder_name
    categories = {}

    for subfolder in root.iterdir():
        if subfolder.is_dir() and \
                subfolder.name.lower() not in ["cli", "utils", "core"] and \
                "__" not in subfolder.name:  # Removes __pycache__
            categories[subfolder.name] = subfolder.resolve()

    return categories


def find_module(name: str, is_email: bool = False) -> List[ModuleType]:
    name = name.lower()

    return [
        module
        for category_path in load_categories(is_email).values()
        for module in load_modules(category_path)
        if module.__name__.split(".")[-1].lower() == name
    ]


def find_category(module: ModuleType) -> str | None:

    module_file = getattr(module, '__file__', None)
    if not module_file:
        return None

    category = Path(module_file).parent.name.lower()
    if category in load_categories(False) or category in load_categories(True):
        return category.capitalize()

    return None


def generate_permutations(username: str, pattern: str, limit: int | None = None, is_email: bool = False) -> List[str]:
    """
    Generate all order-based permutations of characters in `pattern`
    appended after `username`.
    """

    if limit and limit <= 0:
        return []

    permutations_set = {username}
    chars = list(pattern)

    domain = ""
    if is_email:
        username, domain = username.strip().split("@")

    # generate permutations of length 1 → len(chars)
    for r in range(len(chars)):
        for combo in permutations(chars, r):
            new = username + ''.join(combo)
            if is_email:
                new += "@" + domain
            permutations_set.add(new)
            if limit and len(permutations_set) >= limit:
                return sorted(permutations_set)

    return sorted(permutations_set)
