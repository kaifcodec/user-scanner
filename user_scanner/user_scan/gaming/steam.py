from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_steam(user):
    url = f"https://steamcommunity.com/id/{user}/"
    show_url = f"https://steamcommunity.com/id/{user}/"

    def process(response):
        if response.status_code == 200:
            if "Error</title>" in response.text:
                return Result.available()
            else:
                return Result.taken()

        return Result.error("Invalid status code")

    return generic_validate(url, process, show_url=show_url)
