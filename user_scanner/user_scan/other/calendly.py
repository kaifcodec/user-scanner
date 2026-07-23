from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_calendly(user):
    if "." in user:
        return Result.error("Username cannot contain periods")

    api_url = f"https://calendly.com/api/booking/profiles/{user}"
    show_url = f"https://calendly.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    try:
        response = make_request(api_url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            data = response.json()
            
            extra = {}
            if name := data.get("name"):
                extra["name"] = name
            if description := data.get("description"):
                extra["description"] = description
            if avatar := data.get("avatar_url"):
                extra["avatar"] = avatar
            if org := data.get("organization_uuid"):
                extra["organization_uuid"] = org
                
            return Result.taken(extra=extra, url=show_url)
            
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
            
    except Exception as e:
        return Result.error(e, url=show_url)
