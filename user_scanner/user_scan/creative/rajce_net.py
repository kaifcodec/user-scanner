import urllib.parse

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_rajce_net(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = "https://{username}.rajce.idnes.cz/".replace("{username}", encoded_user)
    show_url = f"https://{encoded_user}.rajce.idnes.cz/"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        status = response.status_code
        text = response.text
        if any(ab in text for ab in ['Uživatel neexistuje']):
            return Result.available(url=show_url)

        if status == 200 and any(ps in text for ps in ['"user":{"username":"']):
            return Result.taken(url=show_url)

        return Result.error(f"Unexpected response status {status}")

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=show_url,
        follow_redirects=True,
    )
