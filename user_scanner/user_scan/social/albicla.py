from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_albicla(user):
    url = f"https://albicla.com/{user}/post/1"
    show_url = f"https://albicla.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
    }

    def process(response):
        if (
            response.status_code == 500
            or "500 Post tymczasowo niedostępny" in response.text
        ):
            return Result.taken()

        if "404 Nie znaleziono użytkownika" in response.text:
            return Result.available()

        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
