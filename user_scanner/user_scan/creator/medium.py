from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_medium(user):
    url = f"https://medium.com/@{user}"
    show_url = f"https://medium.com/@{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "identity",
        "upgrade-insecure-requests": "1",
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=0, i",
    }

    def process(response):
        if response.status_code == 200:
            html_text = response.text

            username_tag = f'property="profile:username" content="{user}"'

            if username_tag in html_text:
                return Result.taken()
            else:
                return Result.available()
        return Result.error()

    return generic_validate(url, process, show_url=show_url, headers=headers)
