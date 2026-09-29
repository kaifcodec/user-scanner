import urllib.parse

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_dreamstime(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = "https://www.dreamstime.com/{username}_info".replace("{username}", encoded_user)
    show_url = f"https://www.dreamstime.com/{encoded_user}_info"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        status = response.status_code

        if status in (404, 410):
            return Result.available(url=show_url)

        if status == 200:
            return Result.taken(url=show_url)

        return Result.error(f"Unexpected response status {status}")

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=show_url,
        follow_redirects=True,
    )
