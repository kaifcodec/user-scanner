import importlib
import importlib.util
from itertools import permutations
from types import ModuleType
from pathlib import Path
from typing import Dict, List, Optional
import random
import threading
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed


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


def validate_proxies(proxy_list: List[str], timeout: int = 5, max_workers: int = 50) -> List[str]:
    """Validate proxies by testing them against google.com. Returns list of working proxies."""
    working_proxies = []
    
    def test_proxy(proxy: str) -> Optional[str]:
        try:
            with httpx.Client(proxy=proxy, timeout=timeout) as client:
                response = client.get("https://www.google.com")
                if response.status_code == 200:
                    return proxy
        except Exception:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_proxy, proxy): proxy for proxy in proxy_list}
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_proxies.append(result)
    
    return working_proxies


class ProxyManager:
    """Thread-safe proxy manager that loads and rotates proxies from a file."""
    
    def __init__(self, proxy_file: str):
        self.proxies: list[str] = []
        self.current_index = 0
        self.lock = threading.Lock()
        self._load_proxies(proxy_file)
    
    def _load_proxies(self, proxy_file: str) -> None:
        """Load proxies from a text file. Supports http://, https://, and socks5:// proxies."""
        try:
            with open(proxy_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Add protocol if not present
                        if not line.startswith(('http://', 'https://', 'socks5://')):
                            line = 'http://' + line
                        self.proxies.append(line)
            
            if not self.proxies:
                raise ValueError("No valid proxies found in file")
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Proxy file not found: {proxy_file}")
        except Exception as e:
            raise Exception(f"Error loading proxies: {e}")
    
    def get_next_proxy(self) -> Optional[str]:
        """Get the next proxy in rotation (round-robin)."""
        if not self.proxies:
            return None
        
        with self.lock:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            return proxy
    
    def get_random_proxy(self) -> Optional[str]:
        """Get a random proxy from the list."""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def count(self) -> int:
        """Return the number of loaded proxies."""
        return len(self.proxies)


# Global proxy manager instance
_proxy_manager: Optional[ProxyManager] = None


def set_proxy_manager(proxy_file: Optional[str]) -> None:
    """Initialize the global proxy manager with a proxy file."""
    global _proxy_manager
    if proxy_file:
        _proxy_manager = ProxyManager(proxy_file)
    else:
        _proxy_manager = None


def get_proxy() -> Optional[str]:
    """Get the next proxy from the global proxy manager."""
    if _proxy_manager:
        return _proxy_manager.get_next_proxy()
    return None


def get_proxy_count() -> int:
    """Get the count of loaded proxies."""
    if _proxy_manager:
        return _proxy_manager.count()
    return 0

