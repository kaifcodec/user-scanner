from user_scanner.core.orchestrator import generic_validate, Result


def validate_discogs(user):
    url = f"https://api.discogs.com/users/{user}"
    show_url = f"https://www.discogs.com/user/{user}"

    def process(response):
        if response.status_code == 200 and "\"id\":" in response.text:
            return Result.taken()

        if response.status_code == 404 or "\"message\": \"User does not exist or may have been deleted.\"" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
