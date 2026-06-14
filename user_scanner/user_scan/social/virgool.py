import re
import json
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_virgool(user):
    url = f"https://virgool.io/@{user}"
    show_url = url
    headers = {"User-Agent": get_random_user_agent()}

    try:
        response = make_request(url, headers=headers)
        if response.status_code == 200:
            extra = {}
            match = re.search(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*\\"followersCount\\"(?:[^"\\]|\\.)*")\]', response.text)
            if match:
                try:
                    raw = match.group(1)
                    unquoted = json.loads(raw)
                    
                    fc_match = re.search(r'"followersCount":(\d+)', unquoted)
                    if fc_match: extra['follower_count'] = int(fc_match.group(1))
                        
                    name_match = re.search(r'"name":"([^"]+)"', unquoted)
                    if name_match: extra['fullname'] = name_match.group(1)
                        
                    bio_match = re.search(r'"bio":"([^"]+)"', unquoted)
                    if bio_match: extra['bio'] = bio_match.group(1)
                except Exception:
                    pass
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
