from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_medium(user):
    url = f"https://medium.com/@{user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Encoding': "identity",
        'upgrade-insecure-requests': "1",
        'sec-fetch-site': "none",
        'sec-fetch-mode': "navigate",
        'sec-fetch-user': "?1",
        'sec-fetch-dest': "document",
        'sec-ch-ua': "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': "\"Linux\"",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=0, i"
    }

    def process(response):
        if response.status_code == 200:
            html_text = response.text

            username_tag = f'property="profile:username" content="{user}"'

            if username_tag in html_text:
                return Result.taken()
            else:
                return Result.available()
        return Result.error()

    return generic_validate(url, process, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_medium(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
