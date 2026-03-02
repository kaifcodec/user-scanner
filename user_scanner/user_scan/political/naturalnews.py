from user_scanner.core.orchestrator import generic_validate, Result


def validate_naturalnews(user):
    url = f"https://naturalnews.com/author/{user}/"
    show_url = url

    def process(response):
        if '<div class="VideoPosts">' in response.text:
            return Result.taken()

        if "The page you are looking for cannot be found" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
