from user_scanner.core.orchestrator import status_validate


def validate_instagram(user):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        'X-IG-App-ID': "936619743392459",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Encoding': "gzip, deflate, br",
        'Accept-Language': "en-US,en;q=0.9",
        'X-Requested-With': "XMLHttpRequest",
        'Referer': f"https://www.instagram.com/{user}/",
    }

    return status_validate(url, 404, 200, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_instagram(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
