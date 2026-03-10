from user_scanner.core.orchestrator import generic_validate, Result

def validate_about_me(user):
    url = f"https://about.me/{user}"
    show_url = url

    def process(response):
        if " | about.me" in response.text:
            return Result.taken()

        if "<title>about.me</title>" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
