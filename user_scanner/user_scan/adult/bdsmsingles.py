from user_scanner.core.orchestrator import generic_validate, Result


def validate_bdsmsingles(user):
    url = f"https://www.bdsmsingles.com/members/{user}/"
    show_url = f"https://www.bdsmsingles.com/members/{user}/"

    def process(response):
        if response.status_code == 200 and "<title>Profile" in response.text:
            return Result.taken()

        if response.status_code == 302 or "BDSM Singles" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
