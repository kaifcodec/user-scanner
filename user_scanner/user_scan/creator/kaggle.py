import re
from user_scanner.core.orchestrator import Result, make_request


def validate_kaggle(user):
    url = f"https://www.kaggle.com/{user}"
    show_url = f"https://www.kaggle.com/{user}"

    try:
        response = make_request(url, follow_redirects=True)
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
