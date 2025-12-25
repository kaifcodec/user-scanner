from user_scanner.core.orchestrator import status_validate


def validate_cratesio(user):
    url = f"https://crates.io/api/v1/users/{user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Referer': "https://crates.io/",
        'sec-fetch-mode': "cors",
    }

    return status_validate(url, 404, 200, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_cratesio(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
