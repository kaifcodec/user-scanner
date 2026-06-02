from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_x(user):
    show_url = f"https://x.com/{user}"

    # Try to get rich data from vxtwitter API first
    vx_url = f"https://api.vxtwitter.com/{user}"
    vx_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    
    try:
        vx_response = make_request(vx_url, headers=vx_headers, follow_redirects=True)
        if vx_response.status_code == 200:
            data = vx_response.json()
            extra = {}
            if name := data.get("name"): extra["name"] = name
            if bio := data.get("description"): extra["bio"] = bio
            if loc := data.get("location"): extra["location"] = loc
            if created := data.get("created_at"): extra["created_at"] = created
            if followers := data.get("followers_count"): extra["followers"] = str(followers)
            if following := data.get("following_count"): extra["following"] = str(following)
            if avatar := data.get("profile_image_url"): extra["avatar"] = avatar.replace("_normal", "")
            if protected := data.get("protected"): extra["protected"] = str(protected)
            if tweets := data.get("tweet_count"): extra["tweets"] = str(tweets)
            
            return Result.taken(extra=extra, url=show_url)
    except Exception:
        pass

    # Fallback to checking username availability directly via Twitter API
    url = "https://api.twitter.com/i/users/username_available.json"
    params = {"username": user, "full_name": "John Doe", "email": "johndoe07@gmail.com"}
    headers = {
        "Authority": "api.twitter.com",
        "User-Agent": get_random_user_agent(),
    }

    try:
        response = make_request(url, params=params, headers=headers, follow_redirects=True)
        status = response.status_code

        if status in [401, 403, 429]:
            return Result.error("Twitter rate limit or blocked", url=show_url)

        elif status == 200:
            data = response.json()
            if data.get("valid") is True:
                return Result.available(url=show_url)
            elif data.get("reason") == "taken":
                return Result.taken(url=show_url)
            elif data.get("reason") in ["improper_format", "invalid_username"]:
                return Result.error(f"X says: {data.get('desc')}", url=show_url)

        return Result.error(f"Unexpected status: {status}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
