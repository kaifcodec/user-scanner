from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_openstreetmap(user):
    url = f"https://www.openstreetmap.org/user/{user}"
    show_url = f"https://www.openstreetmap.org/user/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        if "Mapper since" in response.text:
            return Result.taken()
        if "does not exist" in response.text:
            return Result.available()
        return Result.error()

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)