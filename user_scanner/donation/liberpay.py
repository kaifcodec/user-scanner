
import httpx
from httpx import ConnectError, TimeoutException

from ..core.orchestrator import status_validate



def validate_liberapay(user):
    """
    Validates a Liberapay username by checking the HTTP status code of the
    """
    url = f"https://en.liberapay.com/{user}"
    return status_validate(url, 404, 200, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_liberapay(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
