from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_mozilladiscourse(user):
    api_url = f"https://discourse.mozilla.org/u/{user}.json"
    show_url = f"https://discourse.mozilla.org/u/{user}"
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }
    
    resp = make_request(api_url, headers=headers, http2=True)
    if resp.status_code == 404:
        return Result.available(url=show_url)
    elif resp.status_code == 200:
        data = resp.json()
        if "user" in data:
            u_data = data["user"]
            extra = {}
            if "name" in u_data and u_data["name"]:
                extra["name"] = u_data["name"]
            if "created_at" in u_data:
                extra["created_at"] = u_data["created_at"]
            if "trust_level" in u_data:
                extra["trust_level"] = u_data["trust_level"]
            if "title" in u_data and u_data["title"]:
                extra["title"] = u_data["title"]
            if "profile_view_count" in u_data:
                extra["profile_views"] = u_data["profile_view_count"]
            return Result.taken(extra=extra, url=show_url)
            
    raise Exception(f"Unexpected status code {resp.status_code}")
