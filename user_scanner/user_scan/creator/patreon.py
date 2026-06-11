import re
import json
from user_scanner.core.orchestrator import Result, make_request


def validate_patreon(user):
    url = f"https://www.patreon.com/{user}"
    show_url = f"https://www.patreon.com/{user}"

    try:
        response = make_request(url, timeout=15.0, follow_redirects=True)
        if response.status_code == 200:
            html = response.text
            extra = {}
            ld = re.search(r'<script type=\"application/ld\+json\">(.*?)</script>', html, re.DOTALL)
            if ld:
                try:
                    data = json.loads(ld.group(1))
                    if isinstance(data, list): data = data[0]
                    if name := data.get("name"): extra["name"] = name
                    if curl := data.get("url"): extra["url"] = curl
                except Exception:
                    pass
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
