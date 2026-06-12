from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_operaforums(user):
    api_url = f"https://forums.opera.com/api/user/{user}"
    show_url = f"https://forums.opera.com/user/{user}"
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }
    
    resp = make_request(api_url, headers=headers, http2=True)
    if resp.status_code == 404:
        return Result.available(url=show_url)
    elif resp.status_code == 200:
        data = resp.json()
        extra = {}
        if "joindateISO" in data:
            extra["joined_at"] = data["joindateISO"]
        if "reputation" in data:
            extra["reputation"] = data["reputation"]
        if "profileviews" in data:
            extra["profile_views"] = data["profileviews"]
        if "location" in data and data["location"]:
            extra["location"] = data["location"]
        return Result.taken(extra=extra, url=show_url)
        
    raise Exception(f"Unexpected status code {resp.status_code}")
