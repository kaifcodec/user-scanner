from user_scanner.core.orchestrator import generic_validate, Result


def validate_github(user):
    url = f"https://github.com/signup_check/username?value={user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'sec-ch-ua-platform': "\"Linux\"",
        'sec-ch-ua': "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
        'sec-ch-ua-mobile': "?0",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://github.com/signup?source=form-home-signup&user_email=",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    GITHUB_INVALID_MSG = (
        "Username may only contain alphanumeric characters or single hyphens, "
        "and cannot begin or end with a hyphen."
    )

    def process(response):
        if response.status_code == 200:
            return Result.available()

        if response.status_code == 422:
            if GITHUB_INVALID_MSG in response.text:
                return Result.error("Cannot start/end with hyphen or use double hyphens, underscores")

            return Result.taken()

        return Result.error("Unexpected GitHub response report it via issues")

    return generic_validate(url, process, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_github(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
