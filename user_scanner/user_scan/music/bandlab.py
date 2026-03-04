from user_scanner.core.orchestrator import generic_validate, Result


def validate_bandlab(user):
    url = f"https://www.bandlab.com/api/v1.3/users/{user}"
    show_url = f"https://www.bandlab.com/{user}"

    def process(response):
        if response.status_code == 200 and "about" in response.text:
            return Result.taken()

        if response.status_code == 404 or "Couldn't find any matching element" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
