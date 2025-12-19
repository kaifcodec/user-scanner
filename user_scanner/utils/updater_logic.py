import httpx
import re
from pathlib import Path
from user_scanner.core.version import get_pypi_version, load_local_version
from user_scanner.utils.update import update_self

CONFIG_PATH = Path(__file__).parent.parent / "config.py"

def save_config_change(status):
    if not CONFIG_PATH.exists():
        return
    content = CONFIG_PATH.read_text()
    new_content = re.sub(r"auto_update_status\s*=\s*(True|False)", f"auto_update_status = {status}", content)
    CONFIG_PATH.write_text(new_content)

def check_for_updates():
    try:
        from user_scanner import config
    except ImportError:
        return

    if not getattr(config, 'auto_update_status', True):
        return

    try:
        PYPI_URL = "https://pypi.org/pypi/user-scanner/json"
        latest_ver = get_pypi_version(PYPI_URL)
        current_ver, _ = load_local_version()

        if current_ver != latest_ver:
            print(f"\n[!] New version available: {current_ver} -> {latest_ver}")
            choice = input("Do you want to update? (y/n/d: don't ask again): ").strip().lower()
            if choice == "y":
                update_self()
                print("[+] Update successful. Please restart the tool to use the new version.")
                import sys
                sys.exit(0)
            elif choice == "d":
                save_config_change(False)
                print("[*] Auto-update checks disabled.")
    except Exception:
        pass
