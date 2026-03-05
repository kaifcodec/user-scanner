from colorama import Fore
import sys


from user_scanner.core.version import get_pypi_version, load_local_version
from user_scanner.utils.update import update_self
from user_scanner.core.helpers import load_config, save_config_value
# Color configs
R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN
Y = Fore.YELLOW
X = Fore.RESET


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
                save_config_value(False)
                print(f"[{Y}*{X}] {R}Auto-update checks disabled.{X}")

    except Exception as e:
        print(f"[{Y}!{X}] {R}Update check failed{X}: {e}")
