import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request


def validate_linktree(user):
    url = f"https://linktr.ee/{user}"
    show_url = f"https://linktr.ee/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
    }

    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            html = response.text
            extra = {}
            title = re.search(r'<title>([^\|]+)\|', html)
            if title:
                extra["name"] = title.group(1).strip()
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
