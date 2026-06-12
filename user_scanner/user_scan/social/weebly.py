import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_weebly(user):
    url = f"http://{user}.weebly.com/"
    
    headers = {
        "User-Agent": get_random_user_agent(),
    }
    
    resp = make_request(url, headers=headers, http2=True)
    if resp.status_code == 404:
        return Result.available(url=url)
    elif resp.status_code == 200:
        extra = {}
        title_match = re.search(r'<title>(.*?)</title>', resp.text, re.IGNORECASE)
        if title_match:
            extra["title"] = title_match.group(1).strip()
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', resp.text, re.IGNORECASE)
        if desc_match:
            extra["description"] = desc_match.group(1).strip()
        return Result.taken(extra=extra, url=url)
        
    raise Exception(f"Unexpected status code {resp.status_code}")
