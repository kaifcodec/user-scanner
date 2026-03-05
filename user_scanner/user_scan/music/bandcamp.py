from user_scanner.core.orchestrator import generic_validate, Result


def validate_bandcamp(user):
    url = f"https://bandcamp.com/{user}"
    show_url = f"https://bandcamp.com/{user}"

    def process(response):
        if response.status_code == 200 and " collection | Bandcamp</title>" in response.text:
            return Result.taken()

        if response.status_code == 404 or "<h2>Sorry, that something isn’t here.</h2>" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
