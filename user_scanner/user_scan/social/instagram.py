from user_scanner.core.orchestrator import status_validate

def validate_instagram(user):
    url = "https://www.instagram.com/api/v1/users/web_profile_info/"

    params = {
        'username': user
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'sec-ch-ua-full-version-list': "\"Not(A:Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"144.0.7559.132\", \"Google Chrome\";v=\"144.0.7559.132\"",
        'sec-ch-ua-platform': "\"Linux\"",
        'sec-ch-ua': "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
        'sec-ch-ua-model': "\"\"",
        'sec-ch-ua-mobile': "?0",
        'x-ig-app-id': "936619743392459",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-prefers-color-scheme': "dark",
        'x-ig-www-claim': "0",
        'sec-ch-ua-platform-version': "\"\"",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': f"https://www.instagram.com/{user}",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    return status_validate(url, 404, 200, params=params, headers=headers, http2=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_instagram(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! {result.get_reason()}")
