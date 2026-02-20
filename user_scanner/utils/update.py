import subprocess  # nosec B404 - subprocess used with fixed arg lists, shell=False
import sys
from importlib.metadata import PackageNotFoundError, version

from colorama import Fore

def get_version(package_name: str) -> str:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "Unknown"

def update_self():
    print("Updating user-scanner using pip...\n")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "uninstall", "user-scanner", "-y"
        ])  # nosec B603
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "user-scanner"
        ])  # nosec B603
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Failed to update user-scanner: {e}{Fore.RESET}")
        return
    except OSError as e:
        print(f"{Fore.RED}Failed to run updater command: {e}{Fore.RESET}")
        return


    user_scanner_ver = get_version("user-scanner")

    print("\nInstalled Version:")
    print(f"   • user-scanner: {user_scanner_ver}")

if __name__ == "__main__":
    user_scanner_ver = get_version("user-scanner")
    print(user_scanner_ver)

