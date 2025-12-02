
import httpx
from httpx import ConnectError, TimeoutException

from ..core.orchestrator import status_validate



def validate_liberapay(user):
    """
    Validates a Liberapay username by checking the HTTP status code of the
    """
    
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip",
    "Connection": "keep-alive",
    "Host": "en.liberapay.com",
    "Referer": "https://en.liberapay.com/"
    }

    url = f"https://en.liberapay.com/{user}"
    return status_validate(url, 404, 200, headers=headers)

if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_liberapay(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
        