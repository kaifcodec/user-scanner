from user_scanner.core.orchestrator import status_validate, Result


def validate_youtube(user) -> Result:
    url = f"https://m.youtube.com/@{user}"
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Encoding': "identity",
        'sec-ch-dpr': "2.75",
        'sec-ch-viewport-width': "980",
        'sec-ch-ua': "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        'sec-ch-ua-mobile': "?1",
        'sec-ch-ua-full-version': "\"143.0.7499.52\"",
        'sec-ch-ua-arch': "\"\"",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua-platform-version': "\"15.0.0\"",
        'sec-ch-ua-model': "\"I2404\"",
        'sec-ch-ua-bitness': "\"\"",
        'sec-ch-ua-wow64': "?0",
        'sec-ch-ua-full-version-list': "\"Google Chrome\";v=\"143.0.7499.52\", \"Chromium\";v=\"143.0.7499.52\", \"Not A(Brand\";v=\"24.0.0.0\"",
        'sec-ch-ua-form-factors': "\"Mobile\"",
        'upgrade-insecure-requests': "1",
        'x-browser-channel': "stable",
        'x-browser-year': "2025",
        'x-browser-copyright': "Copyright 2025 Google LLC. All Rights reserved.",
        'sec-fetch-site': "none",
        'sec-fetch-mode': "navigate",
        'sec-fetch-user': "?1",
        'sec-fetch-dest': "document",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=0, i"
    }


    return status_validate(url, 404, 200, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_youtube(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        reason = result.get_reason()
        print(f"Error occurred! Reason: {reason}")

