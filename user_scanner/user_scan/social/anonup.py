from user_scanner.core.orchestrator import generic_validate, Result



def validate_anonup(user):
    url = f"https://anonup.com/@{user}"
    show_url = f"https://anonup.com/@{user}"

    def process(response):

        if "Show followings" in response.text:
            return Result.taken()

        if "Page not found!" in response.text or response.status_code == 302:
            return Result.available()

        return Result.error("Unexpected response body!")

    return generic_validate(url, process, show_url=show_url)
