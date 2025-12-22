from pathlib import Path
from colorama import Fore
import sys
import json
import os
from user_scanner.core.version import get_pypi_version, load_local_version
from user_scanner.utils.update import update_self

# Color configs
R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN
Y = Fore.YELLOW
X = Fore.RESET

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


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
        return json.loads(cp.read_text())

    default = {"auto_update_status": True}
    # Ensure parent exists
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(default, indent=2))
    return default


def save_config_change(status: bool, path: str | Path | None = None):
    cp = _get_config_path(path)
    content = load_config(path)
    content["auto_update_status"] = status
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(content, indent=2))


def check_for_updates():
    if not load_config().get("auto_update_status", False):
        return

    try:
        PYPI_URL = "https://pypi.org/pypi/user-scanner/json"
        latest_ver = get_pypi_version(PYPI_URL)
        current_ver, _ = load_local_version()

        if current_ver != latest_ver:
            print(
                f"\n[!] New version available: "
                f"{R}{current_ver}{X} -> {C}{latest_ver}{X}\n"
            )

            choice = input(
                f"{Y}Do you want to update?{X} (y/n/d: {R}don't ask again{X}): "
            ).strip().lower()

            if choice == "y":
                update_self()
                print(f"[{G}+{X}] {G}Update successful. Please restart the tool.{X}")
                sys.exit(0)

            elif choice == "d":
                save_config_change(False)
                print(f"[{Y}*{X}] {R}Auto-update checks disabled.{X}")

    except Exception as e:
        print(f"[{Y}!{X}] {R}Update check failed{X}: {e}")
