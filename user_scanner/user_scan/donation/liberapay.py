from user_scanner.core.orchestrator import generic_validate, Result
import re

def validate_liberapay(user):
    url = f"https://en.liberapay.com/{user}"
    show_url = f"https://en.liberapay.com/{user}"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-Us,pt;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
    }

    def process(response):
        if response.status_code == 200:
            extra = {}
            title_match = re.search(r'<title>([^<]+)</title>', response.text)
            if title_match:
                name = title_match.group(1).split("&#39;s profile")[0].split("'s profile")[0].strip()
                if name.lower() != user.lower():
                    extra["name"] = name
            return Result.taken(extra=extra)
        elif response.status_code in (404, 410):
            return Result.available()
        return Result.error(f"Unexpected status {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers, follow_redirects=True)
