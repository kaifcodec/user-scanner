import urllib.parse

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_imgflip(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = "https://imgflip.com/user/{username}".replace("{username}", encoded_user)
    show_url = f"https://imgflip.com/user/{encoded_user}"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        status = response.status_code
        text = response.text
        if any(ab in text for ab in ['\t\t<h1>404 Page Not Found</h1>\r', '<title>404 Page Not Found</title>\r', 'info-page ibox', '\t\t<p>Or maybe the <a href=', '\t\t<p>Were you looking for the <a href=']):
            return Result.available(url=show_url)

        if status == 200 and any(ps in text for ps in ['u-username', 'user-page', 'user-title', 'user-panel', 'user-joined']):
            return Result.taken(url=show_url)

        return Result.error(f"Unexpected response status {status}")

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=show_url,
        follow_redirects=True,
    )
