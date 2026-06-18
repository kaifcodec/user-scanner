from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_adultforum(user):
    url = f"https://adultforum.gr/{user}-glamour-escorts/"
    show_url = f"https://adultforum.gr/{user}-glamour-escorts/"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response):
        if "Glamour Escorts " in response.text:
            return Result.taken()

        if (
            response.status_code == 404
            or "Page not found - Adult Forum Gr" in response.text
        ):
            return Result.available()

        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
