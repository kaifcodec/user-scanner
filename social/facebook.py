import httpx
from httpx import ConnectError, TimeoutException, TooManyRedirects, codes

def validate_facebook_vanity_url(user: str) -> int:
    """
    Checks if a Facebook vanity URL (username) exists.

    Returns:
        0: Unavailable (User exists)
        1: Available (User does not exist)
        2: Error (Rate-limited, blocked, or connection issue)
    """
    url = f"https://www.facebook.com/{user}"

    # Use comprehensive, common browser headers to reduce the chance of a 400/403 block.
    # The 'cookie' field can be critical, even if empty.
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        'Accept-Encoding': "gzip, deflate, br",
        'Accept-Language': "en-US,en;q=0.9",
        'DNT': "1",
        'Connection': "keep-alive",
        # Adding a fake cookie can sometimes bypass basic bot checks
        'Cookie': 'c_user=123; xs=abc' 
    }
    
    # Facebook uses aggressive anti-bot measures. The request must be very patient.
    try:
        # We use follow_redirects=False to check the initial response/redirect location.
        # This can be more reliable than following to a login page.
        response = httpx.get(
            url, 
            headers=headers, 
            follow_redirects=True, 
            timeout=15.0, # Increased timeout for slow/complex handshake
            # Using HTTP/2 can sometimes help with site compatibility
            http2=True 
        )
        status = response.status_code

        # Log the final URL and status for debugging
        print(f"Final URL: {response.url}")
        print(f"Final Status: {status}")

        # --- Check for existence ---
        
        # 1. User/Page exists: The server responds with 200 OK (the profile page content)
        #    or it redirects to a generic login page/error page AFTER checking the existence.
        #    If the status is 200, the username exists.
        if status == codes.OK:
            return 0  # Unavailable (Username exists)
        
        # 2. User/Page does NOT exist: The server should return a 404 Not Found.
        #    This is the only definitive signal for availability.
        elif status == codes.NOT_FOUND:
            return 1  # Available (Username does not exist)
        
        # 3. Blocked/Error: All other codes (e.g., 400, 403, 500) mean the request was blocked
        #    before the existence check could be performed.
        else:
            # Print the response body if it's small enough (e.g., less than 2KB)
            if len(response.text) < 2048:
                print("\n--- Response Content (Likely Error/Block Page) ---")
                print(response.text)
                print("--------------------------------------------------\n")
            
            # The '400 Bad Request' or '403 Forbidden' you saw previously falls here.
            return 2  # Error (Request Blocked/Rate-limited)

    except (ConnectError, TimeoutException, TooManyRedirects) as e:
        print(f"Network/Connection Error: {type(e).__name__} - {e}")
        return 2 # Error (Network issue)
    except Exception as e:
        print(f"An unexpected error occurred: {type(e).__name__} - {e}")
        return 2 # General Error

if __name__ == "__main__":
   try:
       import httpx
   except ImportError:
       print("Error: 'httpx' library is not installed. Run: pip install httpx")
       exit()

   user = input ("Username?: ").strip()
   
   # You should test with known accounts:
   # Exists: zuck, cocacola, google
   # Not exists: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0_available
   result = validate_facebook_vanity_url(user)

   if result == 1:
      print("\nResult: Available! (Likely does not exist)")
   elif result == 0:
      print("\nResult: Unavailable! (User/Page exists)")
   else:
      print("\nResult: Error/Blocked! (Could not confirm status due to rate limit or block)")
