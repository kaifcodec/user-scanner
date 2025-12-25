from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result
from urllib.parse import quote

def validate_monkeytype(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://api.monkeytype.com/users/checkName/{safe_user}"

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
                return Result.available()
            elif available is False:
                return Result.taken()

        # Surface Monkeytype validation errors (e.g. special characters)
        try:
            data = response.json()
            errors = data.get("validationErrors")
            if errors:
                return Result.error("; ".join(errors))
        except Exception:
            pass

        return Result.error("Invalid status code")

    return generic_validate(url, process, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_monkeytype(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
