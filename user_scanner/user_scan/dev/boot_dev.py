from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

def validate_boot(user):
    url = f"https://www.boot.dev/u/{user}"
    show_url = f"https://boot.dev/u/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://boot.dev/",
    }

    def process(response):
        data = response.text

        if response.status_code == 404:
            return Result.available()
        if "User not found" in data:
            return Result.available()
        if response.status_code == 200 and "__NUXT__" in data and f"publicUser:{user}" in data:
            return Result.taken()
        return Result.error("Unexpected response format")

    return generic_validate(url, process, show_url=show_url, headers=headers)