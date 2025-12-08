from user_scanner.core.orchestrator import status_validate


def validate_youtube(user):
    url = f"https://m.youtube.com/@{user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'device-memory': "4",
        'sec-ch-ua': "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
        'sec-ch-ua-mobile': "?1",
        'sec-ch-ua-full-version': "\"141.0.7390.111\"",
        'sec-ch-ua-arch': "\"\"",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua-platform-version': "\"15.0.0\"",
        'sec-ch-ua-bitness': "\"\"",
        'sec-ch-ua-wow64': "?0",
        'sec-ch-ua-full-version-list': "\"Google Chrome\";v=\"141.0.7390.111\", \"Not?A_Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"141.0.7390.111\"",
        'sec-ch-ua-form-factors': "\"Mobile\"",
        'upgrade-insecure-requests': "1",
        'sec-fetch-site': "none",
        'sec-fetch-mode': "navigate",
        'sec-fetch-user': "?1",
        'sec-fetch-dest': "document",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=0, i"
    }

    status_validate(url, 404, 200, headers=headers, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_youtube(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
