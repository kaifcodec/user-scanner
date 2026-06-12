from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_mixcloud(user):
    api_url = f"https://api.mixcloud.com/{user}/"
    show_url = f"https://www.mixcloud.com/{user}/"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    try:
        response = make_request(api_url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            data = response.json()
            
            # If the user doesn't exist, mixcloud API typically returns 404, 
            # but sometimes JSON contains an error key.
            if "error" in data:
                return Result.available(url=show_url)

            extra = {}
            if name := data.get("name"):
                extra["name"] = name
            if follower_count := data.get("follower_count"):
                extra["followers"] = str(follower_count)
            if following_count := data.get("following_count"):
                extra["following"] = str(following_count)
            if pictures := data.get("pictures", {}):
                # Try large, fallback to thumbnail or small
                if avatar := pictures.get("large") or pictures.get("thumbnail") or pictures.get("small"):
                    extra["avatar"] = avatar
                
            return Result.taken(extra=extra, url=show_url)
            
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
            
    except Exception as e:
        return Result.error(e, url=show_url)
