from colorama import Fore, Style, init
from ..core.version import load_local_version


version, version_type = load_local_version()
init(autoreset=True)
C_RED = Fore.RED + Style.BRIGHT
C_CYAN = Fore.CYAN + Style.BRIGHT
C_GREEN = Fore.GREEN + Style.BRIGHT
C_WHITE = Fore.WHITE + Style.BRIGHT
C_MAGENTA = Fore.MAGENTA + Style.BRIGHT
BANNER_ASCII = fr"""{C_CYAN}      _   _ ___  ___ _ __      ___  ___ __ _ _ __  _ __   ___ _ __
     | | | / __|/ _ \ '__|____/ __|/ __/ _` | '_ \| '_ \ / _ \ '__|
     | |_| \__ \  __/ | |_____\__ \ (_| (_| | | | | | | |  __/ |
      \__,_|___/\___|_|       |___/\___\__,_|_| |_|_| |_|\___|_| Version: {version}
{Style.RESET_ALL}""".strip()


WEB_APP_URL = "https://user-scanner.app"


def print_banner():
    print(BANNER_ASCII)
    print(f"      {C_CYAN}🌐 Web App:{Style.RESET_ALL} {WEB_APP_URL}\n")


if __name__ == "__main__":
    print_banner()
