from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result
from urllib.parse import quote
from user_scanner.core.helpers import get_random_user_agent

def validate_monkeytype(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://api.monkeytype.com/users/checkName/{safe_user}"
    show_url = "https://monkeytype.com"

    headers = {
        "User-Agent": get_random_user_agent(),
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
        except ValueError:
            return Result.error("Invalid status code")

        if isinstance(data, dict):
            errors = data.get("validationErrors")
            if errors:
                return Result.error("; ".join(errors))

        return Result.error("Invalid status code")

    return generic_validate(url, process, show_url=show_url, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_monkeytype(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")