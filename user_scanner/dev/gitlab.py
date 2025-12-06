from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_gitlab(user):
    url = f"https://gitlab.com/users/{user}/exists"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'X-Requested-With': "XMLHttpRequest",
        'Referer': "https://gitlab.com/users/sign_up",
    }

    def process(response):
        if response.status_code == 200:
            data = response.json()
            if 'exists' in data:
                # Corrected: Compare against Python boolean True/False
                # AVAILABLE (return 1) if "exists": true
                if data['exists'] is False:
                    return Result.available()
                # UNAVAILABLE (return 0) if "exists": false
                elif data['exists'] is True:
                    return Result.taken()
        return Result.error("Invalid status code")

    return generic_validate(url, process, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_gitlab(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
