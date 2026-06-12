from user_scanner.core.orchestrator import Result, make_request

def validate_kick(user):
    api_url = f"https://kick.com/api/v2/channels/{user}"
    show_url = f"https://kick.com/{user}"

    # Kick often uses aggressive Cloudflare blocking, so we'll use a more standard browser User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    try:
        response = make_request(api_url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            data = response.json()
            
            extra = {}
            if user_id := data.get("id"):
                extra["id"] = str(user_id)
            if slug := data.get("slug"):
                extra["slug"] = slug
            if "is_banned" in data:
                extra["is_banned"] = str(data["is_banned"])
                
            return Result.taken(extra=extra, url=show_url)
            
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
            
    except Exception as e:
        return Result.error(e, url=show_url)
