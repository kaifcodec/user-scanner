import importlib
import importlib.util
from types import ModuleType
from pathlib import Path
from typing import Dict, List, Optional
import inspect
import json
import os
import random
import threading
import functools
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable

import httpx

LOUD_MODULES: Dict[str, List[str]] = {
    "user": [],
    "email": [
        "leetcode",
        "instagram",
        "netflix",
        "sexvid",
        "made_porn",
        "flirtbate",
        "polarsteps",
        "babestation",
        "flipkart",
    ],
}

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


@dataclass(frozen=True)
class ScanConfig:
    allow_loud: bool = False
    no_nsfw: bool = False
    only_found: bool = False
    verbose: bool = False


def get_site_name(module) -> str:
    name = module.__name__.split(".")[-1].capitalize().replace("_", ".")
    if name == "X":
        return "X (Twitter)"
    return name


@functools.lru_cache(maxsize=None)
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


@functools.lru_cache(maxsize=None)
def load_categories(is_email: bool = False, no_nsfw: bool = False) -> Dict[str, Path]:
    folder_name = "email_scan" if is_email else "user_scan"
    root = Path(__file__).resolve().parent.parent / folder_name
    categories = {}

    for subfolder in root.iterdir():
        if (
            subfolder.is_dir()
            and subfolder.name.lower() not in ["cli", "utils", "core"]
            and "__" not in subfolder.name  # Removes __pycache__
        ):
            if no_nsfw and subfolder.name == "adult":
                continue
            categories[subfolder.name] = subfolder.resolve()

    return categories


def is_loud(name: str, is_email: bool = False) -> bool:
    key = "email" if is_email else "user"
    return name.lower() in LOUD_MODULES[key]


def get_scan_func(module) -> Optional[Callable[[str], Any]]:
    for attr_name in dir(module):
        if not attr_name.startswith("validate_"):
            continue

        f = getattr(module, attr_name)
        if inspect.isfunction(f) or inspect.iscoroutinefunction(f):
            return f
    return None


def find_module(name: str, is_email: bool = False, no_nsfw: bool = False) -> List[ModuleType]:
    name = name.lower()

    return [
        module
        for category_path in load_categories(is_email, no_nsfw).values()
        for module in load_modules(category_path)
        if module.__name__.split(".")[-1].lower() == name
    ]


def find_category(module: ModuleType) -> str | None:
    module_file = getattr(module, "__file__", None)
    if not module_file:
        return None

    category = Path(module_file).parent.name.lower()
    if category in load_categories(False) or category in load_categories(True):
        return category.capitalize()

    return None


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
        """Load proxies from a text file. Keep explicit schemes, default to http:// when missing."""
        try:
            with open(proxy_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Keep explicit schemes (http://, socks5://, socks5h://, etc.).
                        # Only prepend http:// when no scheme is provided.
                        if "://" not in line:
                            line = "http://" + line
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


# Function to return random user agent


def get_random_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 15; Pixel 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
    ]
    """return random"""
    random_agent = random.choice(agents)
    return random_agent


def _get_config_path(path: str | Path | None = None) -> Path:
    """
    Determine the config path in this order:
      1. explicit path argument (if provided)
      2. environment variable USER_SCANNER_CONFIG (if set)
      3. default CONFIG_PATH
    """
    if path:
        return Path(path)
    env = os.environ.get("USER_SCANNER_CONFIG")
    if env:
        return Path(env)
    return CONFIG_PATH


def load_config(path: str | Path | None = None) -> dict:
    cp = _get_config_path(path)
    if cp.exists():
        try:
            return json.loads(cp.read_text())
        except json.JSONDecodeError:
            # This prevents the crash on corrupted JSON
            pass

    default = {
        "auto_update_status": True,
        "auto_hudson_prompt": True
    }
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(default, indent=2))
    return default



def save_config_value(key: str, value: Any, path: str | Path | None = None):
    """Generic helper to update any specific key in the config."""
    cp = _get_config_path(path)
    content = load_config(path)
    content[key] = value
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(content, indent=2))

