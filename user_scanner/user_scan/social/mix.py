from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.result import Result
from user_scanner.core.orchestrator import generic_validate


def validate_mix(user):
    url = f"https://mix.com/{user}"
    show_url = f"https://mix.com/{user}"
    headers = {
        "User-Agent": get_random_user_agent(),
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            return Result.taken()
        else:
            return Result.error(f"HTTP {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
