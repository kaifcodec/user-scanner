from user_scanner.core.orchestrator import generic_validate, Result


def validate_bentbox(user):
    url = f"https://bentbox.co/{user}"
    show_url = f"https://bentbox.co/{user}"

    def process(response):
        if response.status_code == 200 and "user_bar" in response.text:
            return Result.taken()

        if "user is currently not available" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
