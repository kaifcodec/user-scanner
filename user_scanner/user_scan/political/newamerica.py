from user_scanner.core.orchestrator import generic_validate, Result


def validate_newamerica(user):
    url = f"https://www.newamerica.org/our-people/{user}/"
    show_url = url

    def process(response):
        if f'href="http://newamerica.org/our-people/{user}/"' in response.text:
            return Result.taken()

        if "Page not found" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
