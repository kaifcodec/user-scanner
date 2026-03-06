from user_scanner.core.orchestrator import generic_validate, Result


def validate_freesound(user):
    url = f"https://freesound.org/people/{user}/section/stats/?ajax=1"
    show_url = f"https://freesound.org/people/{user}/"

    def process(response):
        if response.status_code == 200 and "forum posts" in response.text.lower():
            return Result.taken()

        if response.status_code == 404 or "Page not found" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
