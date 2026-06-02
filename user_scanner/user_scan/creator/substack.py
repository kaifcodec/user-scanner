import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request


def validate_substack(user: str) -> Result:
    if not (4 <= len(user) <= 32):
        return Result.error("Length must be 4-32 characters")

    if not re.match(r"^[a-z0-9]+$", user):
        if re.search(r"[A-Z]", user):
            return Result.error("Use lowercase letters only")
        return Result.error("Usernames can only contain lowercase letters and numbers")

    url = f"https://{user}.substack.com"
    show_url = f"https://{user}.substack.com"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "identity",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=0, i",
    }

    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            html = response.text
            extra = {}
            import json
            ld = re.search(r'<script type=\"application/ld\+json\">(.*?)</script>', html, re.DOTALL)
            if ld:
                try:
                    data = json.loads(ld.group(1))
                    if isinstance(data, list): data = data[0]
                    if name := data.get("name"): extra["name"] = name
                except:
                    pass
            if "name" not in extra:
                title = re.search(r'<title>([^<]+)</title>', html)
                if title and "|" in title.group(1):
                    extra["name"] = title.group(1).split("|")[0].strip()
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
