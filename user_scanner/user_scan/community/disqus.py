from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_disqus(user):
    api_url = f"https://disqus.com/api/3.0/users/details?user=username%3A{user}&attach=userFlaggedUser&api_key=E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F"
    show_url = f"https://disqus.com/by/{user}/"
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }
    
    resp = make_request(api_url, headers=headers, http2=True)
    if resp.status_code == 200:
        try:
            data = resp.json()
            if "response" in data and "id" in data["response"]:
                user_data = data["response"]
                extra = {}
                for key in ["id", "name", "numFollowers", "numFollowing", "numPosts", "location", "joinedAt", "rep"]:
                    if key in user_data and user_data[key]:
                        extra[key] = user_data[key]
                return Result.taken(extra=extra, url=show_url)
        except Exception:
            pass
    return Result.available(url=show_url)
