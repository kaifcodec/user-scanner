from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_medium(user):
    url = f"https://medium.com/@{user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        'Accept': "text/html",
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
        print("Error occurred!")
