from user_scanner.core.orchestrator import generic_validate


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

    def process(response):
        if response.status_code == 200:
            data = response.json()
            # Expected shape:
            # { "message": "string", "data": { "available": true/false } }
            payload = data.get("data", {})
            available = payload.get("available")

            if available is True:
                return 1
            elif available is False:
                return 0
        return 2

    return generic_validate(url, process, headers=headers)


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
