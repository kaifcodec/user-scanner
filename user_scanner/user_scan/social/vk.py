from user_scanner.core.orchestrator import generic_validate, Result


def validate_vk(user):
    url = f"https://vk.com/{user}"
    show_url = f"https://vk.com/{user}" 

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            return Result.taken()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
