from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_spotify(user):
    api_url = f"https://api.stats.fm/api/v1/users/{user}"
    show_url = f"https://open.spotify.com/user/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    try:
        response = make_request(api_url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            data = response.json()
            item = data.get("item", {})
            
            extra = {}
            if name := item.get("displayName"):
                extra["name"] = name
            if image := item.get("image"):
                extra["image"] = image
            if created_at := item.get("createdAt"):
                extra["created_at"] = created_at
            if timezone := item.get("timezone"):
                extra["timezone"] = timezone
                
            # Extra profile metadata
            profile = item.get("profile", {})
            if bio := profile.get("bio"):
                extra["bio"] = bio
            if pronouns := profile.get("pronouns"):
                extra["pronouns"] = pronouns
                
            # Subscription info
            if "isPro" in item:
                extra["is_pro"] = str(item["isPro"])
            if "isPlus" in item:
                extra["is_plus"] = str(item["isPlus"])

            return Result.taken(extra=extra, url=show_url)
            
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
            
    except Exception as e:
        return Result.error(e, url=show_url)
