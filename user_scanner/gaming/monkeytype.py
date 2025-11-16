import httpx
from httpx import ConnectError, TimeoutException
import json

def validate_monkeytype(user: str) -> int:

    url = f"https://api.monkeytype.com/users/checkName/{user}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "identity",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = httpx.get(url, headers=headers, timeout=3.0)
        status = response.status_code

        if status == 200:
            data = response.json()
            # Expected shape:
            # { "message": "string", "data": { "available": true/false } }
            payload = data.get("data", {})
            available = payload.get("available")

            if available is True:
                return 1
            elif available is False:
                return 0
            else:
                return 2
        else:
            return 2

    except (ConnectError, TimeoutException):
        return 2
    except json.JSONDecodeError:
        return 2
    except Exception:
        return 2


if __name__ == "__main__":
    try:
        import httpx  # noqa: F401
    except ImportError:
        print("Error: 'httpx' library is not installed.")
        raise SystemExit(1)

    user = input("Username?: ").strip()
    result = validate_monkeytype(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
