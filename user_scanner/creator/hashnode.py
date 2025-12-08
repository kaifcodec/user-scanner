import httpx
from user_scanner.core.result import Result


def validate_hashnode(user):
    url = "https://hashnode.com/utility/ajax/check-username"

    payload = {
        "username": user,
        "name": "Dummy Dummy"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Content-Type': "application/json",
        'Origin': "https://hashnode.com",
        'Referer': "https://hashnode.com/signup",
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=3.0)

        if response.status_code == 200:
            data = response.json()

            if 'status' in data:
                if data['status'] == 1:
                    return Result.available()
                elif data['status'] == 0:
                    return Result.taken()

            return Result.error("Status not found")

        else:
            return Result.error("Invalid status code")

    except Exception as e:
        return Result.error(e)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_hashnode(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
