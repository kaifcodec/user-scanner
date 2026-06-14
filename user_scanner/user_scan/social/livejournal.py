import re
import json
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_livejournal(user):
    url = f"https://{user}.livejournal.com"
    show_url = url
    headers = {"User-Agent": get_random_user_agent()}

    try:
        response = make_request(url, headers=headers)
        if response.status_code == 200:
            extra = {}
            match = re.search(r'Site\.journal\s*=\s*({.+?});', response.text)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if 'id' in data: extra['uid'] = data['id']
                    if 'display_username' in data: extra['name'] = data['display_username']
                    if 'is_paid' in data: extra['is_paid'] = data['is_paid']
                    if 'is_community' in data: extra['is_community'] = data['is_community']
                except Exception:
                    pass
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        elif response.status_code in [403, 410, 302, 301]:
            # Non-existent user might redirect or give 404
            # If 403, usually suspended (which means taken)
            if response.status_code == 403:
                return Result.taken(extra={"status": "suspended or forbidden"}, url=show_url)
            # Fallback for others
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
