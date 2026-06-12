from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_dailymotion(user):
    api_url = f"https://api.dailymotion.com/user/{user}?fields=id,username,screenname,description,avatar_720_url,cover_250_url,followers_total,following_total,videos_total,country,created_time,verified,url"
    show_url = f"https://www.dailymotion.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    try:
        response = make_request(api_url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            data = response.json()
            
            if "error" in data:
                # Dailymotion API can return 200 with an error object
                if data["error"].get("code") == 404:
                    return Result.available(url=show_url)
                return Result.error(data["error"].get("message", "Unknown error"), url=show_url)

            extra = {}
            if screenname := data.get("screenname"):
                extra["screenname"] = screenname
            if description := data.get("description"):
                extra["description"] = description
            if avatar := data.get("avatar_720_url"):
                extra["avatar"] = avatar
            if followers := data.get("followers_total"):
                extra["followers"] = str(followers)
            if videos := data.get("videos_total"):
                extra["videos"] = str(videos)
            if country := data.get("country"):
                extra["country"] = country
            if verified := data.get("verified"):
                extra["verified"] = str(verified)
                
            return Result.taken(extra=extra, url=show_url)
            
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
            
    except Exception as e:
        return Result.error(e, url=show_url)
