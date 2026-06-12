from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_wikipedia(user):
    # Using formatversion=2 for a cleaner JSON response
    api_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=users&ususers={user}&usprop=editcount|registration|gender&formatversion=2"
    show_url = f"https://en.wikipedia.org/wiki/User:{user}"

    try:
        response = make_request(api_url, follow_redirects=True, http2=True)
        if response.status_code == 200:
            data = response.json()
            users = data.get("query", {}).get("users", [])
            
            if not users:
                return Result.error("Invalid API response format", url=show_url)
                
            user_data = users[0]
            
            # Wikipedia API returns a "missing" key if the user does not exist
            if "missing" in user_data:
                return Result.available(url=show_url)
                
            extra = {}
            if userid := user_data.get("userid"):
                extra["userid"] = str(userid)
            if editcount := user_data.get("editcount"):
                extra["editcount"] = str(editcount)
            if registration := user_data.get("registration"):
                extra["registration"] = registration
            if gender := user_data.get("gender"):
                extra["gender"] = gender
                
            return Result.taken(extra=extra, url=show_url)
            
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
            
    except Exception as e:
        return Result.error(e, url=show_url)
