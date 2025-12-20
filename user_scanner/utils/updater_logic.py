from pathlib import Path
from colorama import Fore
import sys
import json
from user_scanner.core.version import get_pypi_version, load_local_version
from user_scanner.utils.update import update_self

# Color configs
R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN
Y = Fore.YELLOW
X = Fore.RESET

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())

    default = {"auto_update_status": True}
    CONFIG_PATH.write_text(json.dumps(default, indent=2))
    return default


def save_config_change(status: bool):
    content = load_config()
    content["auto_update_status"] = status
    CONFIG_PATH.write_text(json.dumps(content, indent=2))


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
        print(f"[!] Update check failed: {e}")
