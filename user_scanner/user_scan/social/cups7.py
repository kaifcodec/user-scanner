from user_scanner.core.orchestrator import generic_validate, Result

def validate_7cups(user):
    url = f"https://www.7cups.com/@{user}"
    show_url = url

    def process(response):
        if "Profile - 7 Cups" in response.text:
            return Result.taken()

        if "The content you're attempting to access could not be" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
