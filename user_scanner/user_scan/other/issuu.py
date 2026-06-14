import json
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_issuu(user: str) -> Result:
    url = f"https://issuu.com/{user}"
    api_url = f"https://issuu.com/query?format=json&_=3210224608766&profileUsername={user}&action=issuu.user.get_anonymous"
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
        "Referer": url,
    }
    
    try:
        response = make_request(api_url, headers=headers, follow_redirects=True)
        text = response.text
        
        if response.status_code == 200 and "displayName" in text:
            extra = {}
            try:
                data = response.json()
                profile = data.get("rsp", {}).get("_content", {}).get("profile", {})
                if display_name := profile.get("displayName"):
                    extra["name"] = display_name
                if about := profile.get("about"):
                    extra["bio"] = about
                if location := profile.get("location"):
                    extra["location"] = location
                if website := profile.get("website"):
                    extra["website"] = website
            except json.JSONDecodeError:
                pass
                
            return Result.taken(extra=extra, url=url)
            
        elif response.status_code == 404 or "No such user" in text or "no such user" in text.lower():
            return Result.available(url=url)
            
        return Result.error(f"Unexpected response status: {response.status_code}", url=url)
        
    except Exception as e:
        return Result.error(e, url=url)
