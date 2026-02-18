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


# Function to return random user agent

def get_random_user_agent():
    """List of modern User-Agents:
        Samsung Galaxy S25, Samsung Galaxy S24 Ultra, Samsung Flip, Google Pixel 9 Pro,
        Google Pixel 9, Google Pixel 8 Pro, Google Pixel 8, Motorola Moto G (2025), Redmi Note 13 4G,
        Apple iPhone 16e, Apple iPhone 16 Pro, Apple iPhone 16 Pro Max, Apple iPhone 16,
        Apple iPhone 16 Plus, Apple iPhone 15 Pro, Apple iPhone 14, Microsoft Lumia 650,
        Apple iPad Pro (11 5th Gen), Samsung Galaxy Tab Active5 5G, Amazon Fire HD 8 (2024, 12th Gen),
        Google Pixel C, Windows 10-based PC using Edge browser,
        Chrome OS-based laptop using Chrome browser (Chromebook),
        Mac OS X-based computer using a Safari browser, Linux-based PC using a Firefox browser"""
    agents = ["Mozilla/5.0 (Linux; Android 15; SM-S931B Build/AP3A.240905.015.A2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36",
              "Mozila/5.0 (Linux; Android 14; SM-S928B/DS) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
              "Mozilla/5.0 (Linux; Android 14; SM-F9560 Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36",
              "Mozilla/5.0 (Linux; Android 14; Pixel 9 Pro Build/AD1A.240418.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/124.0.6367.54 Mobile Safari/537.36",
              "Mozilla/5.0 (Linux; Android 14; Pixel 9 Build/AD1A.240411.003.A5; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/124.0.6367.54 Mobile Safari/537.36",
              "Mozilla/5.0 (Linux; Android 15; Pixel 8 Pro Build/AP4A.250105.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36",
              "Mozilla/5.0 (Linux; Android 15; Pixel 8 Build/AP4A.250105.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36",
              "Mozilla/5.0 (Linux; Android 15; moto g - 2025 Build/V1VK35.22-13-2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36",
              "Mozilla/5.0 (Linux; Android 13; 23129RAA4G Build/TKQ1.221114.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36",
              "Mozilla/5.0 (iPhone17,5; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 FireKeepers/1.7.0",
              "Mozilla/5.0 (iPhone17,1; CPU iPhone OS 18_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Mohegan Sun/4.7.4",
              "Mozilla/5.0 (iPhone17,2; CPU iPhone OS 18_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Resorts/4.5.2",
              "Mozilla/5.0 (iPhone17,3; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 FireKeepers/1.6.1",
              "Mozilla/5.0 (iPhone17,4; CPU iPhone OS 18_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Resorts/4.7.5",
              "Mozilla/5.0 (iPhone16,2; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Resorts/4.7.5",
              "Mozilla/5.0 (iPhone14,7; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Mohegan Sun/4.7.3",
              "Mozilla/5.0 (Windows Phone 10.0; Android 6.0.1; Microsoft; RM-1152) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Mobile Safari/537.36 Edge/15.15254",
              "Mozilla/5.0 (iPad16,3; CPU OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Tropicana_NJ/5.7.1",
              "Dalvik/2.1.0 (Linux; U; Android 14; SM-X306B Build/UP1A.231005.007)",
              "Dalvik/2.1.0 (Linux; U; Android 11; KFRASWI Build/RS8332.3115N)",
              "Mozilla/5.0 (Linux; Android 7.0; Pixel C Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36",
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
              "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
              "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Safari/605.1.15",
              "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1"]
    """retrun random"""
    random_agent = random.choice(agents)
    return random_agent

