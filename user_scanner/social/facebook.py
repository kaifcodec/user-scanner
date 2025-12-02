
from ..core.orchestrator import status_validate
import re 

def validate_facebook(user:str) -> int:
    """
    Validates a Facebook username using a regex pre-check and then an external status check.
    """
    # 1. Define the Facebook Username Regex Pattern
    # Constraints: 5-50 chars, A-Z, a-z, 0-9, period (.), no leading/trailing/consecutive periods.
    FACEBOOK_REGEX = r"^(?!\.)(?!.*\.\.)[a-zA-Z0-9.]{5,50}(?<!\.)$"

    # 2. Perform the Regex Pre-Check
    if not re.fullmatch(FACEBOOK_REGEX, user):
        
        # --- Determine the specific constraint that failed for the error message ---
        message = "Username failed Facebook's format rules."
        if len(user) < 5 or len(user) > 50:
            message = "Username must be between 5 and 50 characters."
        elif not re.match(r"^[a-zA-Z0-9.]+$", user):
            message = "Username can only contain letters, numbers, and periods."
        elif user.startswith('.') or user.endswith('.'):
            message = "Username cannot start or end with a period."
        elif '..' in user:
            message = "Username cannot have consecutive periods."
        print(f"\tFormat Error: {message}") # Print error before returning 2
        return 2
    else:
        url = f"https://www.facebook.com/{user}"

        headers = {
        "User-Agent": "Mozilla/5.0 ... Safari/537.36",#"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
    }


        # 404 -> available, 200 -> taken
        return status_validate(url, 404, 200, headers=headers, follow_redirects=True)

if __name__=="__main__":
    user = input("Username?: ").strip()
    result = validate_facebook(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
