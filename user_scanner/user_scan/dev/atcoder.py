from user_scanner.core.orchestrator import generic_validate, Result

def validate_atcoder(user):
    url = f"https://atcoder.jp/api/users/exists/?userScreenName={user}"
    show_url = f"https://atcoder.jp/users/{user}"

    def process(response):
        if response.status_code == 200:
            if response.text.strip().lower() == "true":
                return Result.taken()
            if response.text.strip().lower() == "false":
                return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
