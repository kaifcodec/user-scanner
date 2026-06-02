import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request


def validate_dribbble(user):
    url = f"https://dribbble.com/{user}"
    show_url = f"https://dribbble.com/{user}"

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
            name_match = re.search(r'<meta name=\"description\" content=\"([^\|]+?)\s*\|', html)
            if name_match:
                extra['name'] = name_match.group(1).strip()
                
            bio_match = re.search(r'<meta name=\"description\" content=\"[^\|]+\|\s*([^\|]+?)\s*\|', html)
            if bio_match:
                extra['bio'] = bio_match.group(1).strip()
                
            loc_match = re.search(r'class=\"location[^\"]*\">([^<]+)</span>', html, re.I)
            if loc_match:
                extra['location'] = loc_match.group(1).strip()
                
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status code: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
