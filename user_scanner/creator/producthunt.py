from user_scanner.core.orchestrator import status_validate


def validate_producthunt(user):
    url = f"https://www.producthunt.com/@{user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Encoding': "gzip, deflate, br",
        'Accept-Language': "en-US,en;q=0.9",
    }

    status_validate(url, 404, 200, headers=headers, follow_redirects=True)

if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_producthunt(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
