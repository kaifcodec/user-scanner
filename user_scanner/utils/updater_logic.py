from pathlib import Path
import json
from user_scanner.core.version import get_pypi_version, load_local_version
from user_scanner.utils.update import update_self

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())

    default = {
        "auto_update_status": True
    }
    CONFIG_PATH.write_text(json.dumps(default))
    return default


def save_config_change(status):
    content = load_config()
    content["auto_update_status"] = status
    CONFIG_PATH.write_text(json.dumps(content))


def check_for_updates():
    if load_config().get("auto_update_status", False) != True:
        return

    try:
        PYPI_URL = "https://pypi.org/pypi/user-scanner/json"
        latest_ver = get_pypi_version(PYPI_URL)
        current_ver, _ = load_local_version()

        if current_ver != latest_ver:
            print(
                f"\n[!] New version available: {current_ver} -> {latest_ver}")
            choice = input(
                "Do you want to update? (y/n/d: don't ask again): ").strip().lower()
            if choice == "y":
                update_self()
                print(
                    "[+] Update successful. Please restart the tool to use the new version.")
                import sys
                sys.exit(0)
            elif choice == "d":
                save_config_change(False)
                print("[*] Auto-update checks disabled.")
    except Exception:
        pass
