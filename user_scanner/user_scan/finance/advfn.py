from user_scanner.core.orchestrator import generic_validate, Result

def validate_advfn(user):
    url = f"https://uk.advfn.com/forum/profile/{user}"
    show_url = url

    def process(response):
        if "Profile | ADVFN" in response.text:
            return Result.taken()

        if "ADVFN ERROR - Page Not Found" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
