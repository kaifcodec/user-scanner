import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_wordpress(user):
    url = f"https://profiles.wordpress.org/{user}/"
    
    headers = {
        "User-Agent": get_random_user_agent(),
    }
    
    resp = make_request(url, headers=headers, http2=True)
    if resp.status_code == 404:
        return Result.available(url=url)
    elif resp.status_code == 200:
        extra = {}
        title_match = re.search(r'<title>(.*?)</title>', resp.text, re.IGNORECASE)
        if title_match and "user profile" in title_match.group(1).lower():
            name_match = re.search(r'class="user-name"[^>]*>([^<]+)</div>', resp.text)
            if name_match:
                extra["name"] = name_match.group(1).strip()
            return Result.taken(extra=extra, url=url)
            
    return Result.error(f"Unexpected response status: {resp.status_code}")
