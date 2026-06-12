from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_scratch(user):
    api_url = f"https://api.scratch.mit.edu/users/{user}"
    show_url = f"https://scratch.mit.edu/users/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    try:
        response = make_request(api_url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            data = response.json()
            
            extra = {}
            if user_id := data.get("id"):
                extra["id"] = str(user_id)
            if history := data.get("history", {}):
                if joined := history.get("joined"):
                    extra["joined"] = joined
            if profile := data.get("profile", {}):
                if images := profile.get("images", {}):
                    if avatar := images.get("90x90"):
                        extra["avatar"] = avatar
                if country := profile.get("country"):
                    extra["country"] = country
                
            return Result.taken(extra=extra, url=show_url)
            
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
            
    except Exception as e:
        return Result.error(e, url=show_url)
