import sys
import json
from colorama import Fore, Style
from user_scanner.core.helpers import load_config, _get_config_path

# Color configs
R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN
Y = Fore.YELLOW
X = Style.RESET_ALL


def update_loud_module_preference(show_prompt: bool):
    """Updates the config file using the existing helper logic."""
    cp = _get_config_path()
    content = load_config()
    content["auto_loud_single_module_prompt"] = show_prompt
    cp.write_text(json.dumps(content, indent=2))


def check_loud_module_permission(site_name: str, target: str) -> bool:
    """Disclaimers and prompts based on user config. Returns True if the
    module should run, False if it should be skipped."""
    config = load_config()

    # If the user already set this to false, skip the prompt and run
    if not config.get("auto_loud_single_module_prompt", True):
        print(f"{Y}[i] '{site_name}' allowed via saved preference.{X}")
        return True

    # Non-interactive session, nowhere to prompt, don't risk a silent notify
    if not sys.stdin.isatty():
        print(f"{Y}[i] '{site_name}' is a loud module and was skipped "
              f"(non-interactive session, pass --allow-loud to run it).{X}")
        return False

    print(f"\n{Y}[!] LOUD MODULE WARNING:{X}")
    print(f"    '{site_name}' is known to notify the target when queried (e.g. password reset email).")
    print(f"    By proceeding, '{C}{target}{Y}' may receive a password reset or verification email.{X}")

    while True:
        choice = input(f"\n{C}Run '{site_name}' anyway? (y/n/d for don't ask again): {X}").lower().strip()
        if choice == 'y':
            return True
        elif choice == 'n':
            print(f"{Y}[i] '{site_name}' skipped.{X}")
            return False
        elif choice == 'd':
            update_loud_module_preference(False)
            print(f"{G}[+] Preference saved. You won't be prompted again for loud modules.{X}")
            return True
        else:
            print(f"{R}[!] Please enter 'y', 'n', or 'd'.{X}")
