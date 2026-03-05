from user_scanner.core.orchestrator import generic_validate, Result


def validate_bdsmlr(user):
    user = user.replace(".", "")
    url = f"https://{user}.bdsmlr.com"
    show_url = f"https://{user}.bdsmlr.com"

    def process(response):
        if response.status_code == 200 and "login" in response.text:
            return Result.taken()

        if "This blog doesn't exist." in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
