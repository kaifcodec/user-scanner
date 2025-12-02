from ..core.orchestrator import status_validate

def validate_facebook(username:str) -> int:
    """
    Validates a Facebook username using a regex pre-check and then an external status check.
    """
    FACEBOOK_REGEX = r"^(?!\.)(?!.*\.\.)[a-zA-Z0-9.]{5,50}(?<!\.)$"

    # 2. Perform the Regex Pre-Check
    if not re.fullmatch(FACEBOOK_REGEX, username):
        # --- Determine the specific constraint that failed for the error message ---
        message = "Username failed Facebook's format rules."
        if len(username) < 5 or len(username) > 50:
            message = "Username must be between 5 and 50 characters."
        elif not re.match(r"^[a-zA-Z0-9.]+$", username):
            message = "Username can only contain letters, numbers, and periods."
        elif username.startswith('.') or username.endswith('.'):
            message = "Username cannot start or end with a period."
        elif '..' in username:
            message = "Username cannot have consecutive periods."
            
        print(f"\tFormat Error: {message}")
        return 2
    else:
        # Example URL structure for Facebook (based on typical validation endpoints)
        # Note: This URL is illustrative, actual Facebook validation might require specific headers/requests.
        url = f"https://www.facebook.com/{username}"

         headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
         }
        return status_validate(url, 404, 200, headers=headers, follow_redirects=True)
