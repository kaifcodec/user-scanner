import re
from colorama import Fore, Style
from user_scanner.core.result import Result
from user_scanner.core.helpers import is_valid_email

R = Fore.RED
G = Fore.GREEN
C = Fore.CYAN
Y = Fore.YELLOW
X = Style.RESET_ALL

def extract_emails(results: list[Result]) -> list[str]:
    """Extract emails from the extra dictionary of username scan results."""
    emails = set()
    for result in results:
        if not result.is_found():
            continue
        for key, value in result.extra.items():
            if not isinstance(value, str):
                continue
            
            # Check if key implies an email
            if "email" in key.lower() and is_valid_email(value.strip()):
                emails.add(value.strip().lower())
            
            # Sometimes the value itself is a valid email (often buried in bios/descriptions)
            # A simple regex check helps uncover emails in larger text blocks
            matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', value)
            for match in matches:
                if is_valid_email(match):
                    emails.add(match.lower())
                    
    return list(emails)


def extract_usernames(results: list[Result], original_email: str) -> list[str]:
    """Extract usernames from email scan results and the email prefix."""
    usernames = set()
    
    # The part before the @ symbol is often the primary username
    if "@" in original_email:
        prefix = original_email.split("@")[0]
        if prefix:
            usernames.add(prefix)
            
    # Check OSINT module extra fields for exposed usernames
    for result in results:
        if not result.is_found():
            continue
        for key, value in result.extra.items():
            if not isinstance(value, str):
                continue
            
            key_lower = key.lower()
            if "username" in key_lower or "handle" in key_lower:
                # Some modules return raw usernames in these fields
                # We should ignore URLs if they somehow ended up here
                val_strip = value.strip()
                if val_strip and not val_strip.startswith("http"):
                    usernames.add(val_strip)
                    
            # Look for linked social accounts in verified fields
            # For instance, Gravatar might return connected GitHub or Twitter profiles
            if "verified" in key_lower or "accounts" in key_lower or "wallet" in key_lower:
                for regex in [
                    r'github\.com/([^/\s\(\)]+)',
                    r'twitter\.com/([^/\s\(\)]+)',
                    r'paypal\.me/([^/\s\(\)]+)',
                    r'patreon\.com/([^/\s\(\)]+)',
                    r'venmo\.com/(?:u/)?([^/\s\(\)]+)'
                ]:
                    matches = re.findall(regex, value, re.IGNORECASE)
                    for match in matches:
                        # Exclude common false positives like "paypal.me/crypto" or API paths if needed
                        # But for now, grab the clean username
                        usernames.add(match.strip())
                        
            # Some platforms return URLs as values directly. 
            # We can run the same URL regexes on the raw value string to catch them.
            for regex in [
                r'paypal\.me/([^/\s\(\)]+)',
                r'patreon\.com/([^/\s\(\)]+)',
                r'venmo\.com/(?:u/)?([^/\s\(\)]+)'
            ]:
                matches = re.findall(regex, value, re.IGNORECASE)
                for match in matches:
                    usernames.add(match.strip())
                    
    return list(usernames)


def prompt_target_selection(targets: list[str], target_type: str, auto_select: bool = False) -> list[str]:
    """
    Presents a list of extracted targets to the user and asks them to select which ones to scan.
    If auto_select is True, returns all targets without prompting.
    """
    if not targets:
        return []

    if auto_select:
        print(f"\n{G}[+] Auto-selected {len(targets)} extracted {target_type}(s) for cross-scan.{X}")
        return targets
        
    print(f"\n{C}=== EXTRACTED {target_type.upper()}S FOR CROSS-SCAN ==={X}")
    print(f"{Y}[i] Found {len(targets)} potential {target_type}(s). Select which to scan:{X}")
    
    for i, target in enumerate(targets, 1):
        print(f"  {G}[{i}]{X} {target}")
        
    print(f"  {G}[A]{X} All")
    print(f"  {Y}[S]{X} Skip (Cancel cross-scan)")
    
    while True:
        try:
            choice = input(f"\n{C}Select numbers (e.g. 1,3), 'A' for all, or 'S' to skip: {X}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Y}[i] Cross-scan skipped.{X}")
            return []
            
        if not choice or choice == 's' or choice == 'skip':
            print(f"{Y}[i] Cross-scan skipped.{X}")
            return []
            
        if choice == 'a' or choice == 'all':
            return targets
            
        selected = []
        parts = choice.replace(" ", "").split(",")
        valid = True
        
        for part in parts:
            if not part.isdigit():
                valid = False
                break
            idx = int(part)
            if 1 <= idx <= len(targets):
                selected.append(targets[idx - 1])
            else:
                valid = False
                break
                
        if not valid:
            print(f"{R}[!] Invalid selection. Please enter comma-separated numbers (e.g. 1,3), 'A' or 'S'.{X}")
            continue
            
        # Deduplicate selections in case user entered "1,1"
        return list(dict.fromkeys(selected))
