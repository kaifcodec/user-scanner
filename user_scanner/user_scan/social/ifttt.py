from user_scanner.core.orchestrator import generic_validate, Result

def validate_ifttt(user):
    if "." in user:
        return Result.error("Username cannot contain periods")

    url = f"https://ifttt.com/p/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            return Result.taken()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=url, headers=headers)
