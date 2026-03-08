import httpx
import json
from colorama import Fore, Style
from user_scanner.core.helpers import load_config, _get_config_path

# Color configs
R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN
Y = Fore.YELLOW
M = Fore.MAGENTA
X = Style.RESET_ALL

def update_hudson_preference(show_prompt: bool):
    """Updates the config file using your existing helper logic."""
    cp = _get_config_path()
    content = load_config()
    content["auto_hudson_prompt"] = show_prompt
    cp.write_text(json.dumps(content, indent=2))

def check_hudson_permission(target: str) -> bool:
    """Disclaimers and prompts based on user config."""
    config = load_config()

    # If the user already set this to false, skip the prompt and run
    if not config.get("auto_hudson_prompt", True):
        return True

    print(f"\n{Y}[!] PRIVACY NOTICE & DISCLAIMER:{X}")
    print("    Hudson Rock is a third-party intelligence service.")
    print(f"    By proceeding, the identifier '{C}{target}{Y}' will be sent to their API.")
    print(f"    They may log queries. We are not responsible for their data handling.{X}")

    while True:
        choice = input(f"\n{C}Query Hudson Rock? (y/n/d for don't ask again): {X}").lower().strip()
        if choice == 'y':
            return True
        elif choice == 'n':
            print(f"{Y}[i] Hudson Rock scan skipped.{X}")
            return False
        elif choice == 'd':
            update_hudson_preference(False)
            print(f"{G}[+] Preference saved. You won't be prompted again.{X}")
            return True
        else:
            print(f"{R}[!] Please enter 'y', 'n', or 'd'.{X}")

def run_hudson_scan(target: str, is_email: bool = False):
    """
    Fetch and display intelligence from Hudson Rock's OSINT API.
    """
    # Permission check using the new logic
    if not check_hudson_permission(target):
        return

    base_url = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/"
    endpoint = "search-by-email" if is_email else "search-by-username"
    param = "email" if is_email else "username"

    url = f"{base_url}{endpoint}?{param}={target}"

    print(f"\n{M}== HUDSON ROCK INFOSTEALER INTELLIGENCE =={X}")
    print(f"{C}[i] Attribution: Data provided by Hudson Rock (https://www.hudsonrock.com){X}")
    print(f"{C}[*] Querying Hudson Rock for {target}...{X}")

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)

            if response.status_code == 200:
                data = response.json()
                stealers = data.get("stealers", [])

                if not stealers:
                    print(f"{G}[✔] No infostealer infections found for this {param}.{X}")
                    return

                total_stealers = len(stealers)
                print(f"{R}[!] FOUND {total_stealers} INFOSTEALER INFECTION(S) ASSOCIATED WITH THIS {param.upper()}!{X}")

                for i, stealer in enumerate(stealers, 1):
                    print(f"\n  {Y}Infection #{i}:{X}")
                    print(f"    - Stealer Family: {stealer.get('stealer_family', 'Unknown')}")
                    print(f"    - Date Compromised: {stealer.get('date_compromised', 'Unknown')}")
                    print(f"    - Operating System: {stealer.get('operating_system', 'Unknown')}")
                    print(f"    - Computer Name: {stealer.get('computer_name', 'Unknown')}")

                    antiviruses = stealer.get('antiviruses', [])
                    if antiviruses:
                        print(f"    - Antiviruses: {', '.join(antiviruses)}")

                    top_logins = stealer.get('top_logins', [])
                    if top_logins:
                        print(f"    - Sample Logins Found: {', '.join(top_logins[:3])}...")

                print(f"\n{Y}[!] Recommendation: All credentials saved on infected computers are at risk.{X}")
                print(f"{Y}[!] Visit https://www.hudsonrock.com/free-tools for more info.{X}")

            elif response.status_code == 404:
                print(f"{G}[✔] No data found for this {param} in Hudson Rock database.{X}")
            else:
                print(f"{R}[✘] Hudson Rock API error: HTTP {response.status_code}{X}")

    except Exception as e:
        print(f"{R}[✘] Error connecting to Hudson Rock: {e}{X}")
