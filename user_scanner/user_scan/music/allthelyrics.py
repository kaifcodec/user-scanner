import re
from user_scanner.core.orchestrator import Result, make_request

def validate_allthelyrics(user):
    url = f"https://www.allthelyrics.com/forum/member.php?username={user}"
    show_url = f"https://www.allthelyrics.com/forum/members/{user}.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        html = response.text
        
        if "The server is too busy" in html:
            # The vBulletin forum is currently offline/broken for all users
            return Result.error("Forum server is currently down/too busy", url=show_url)
            
        if "Invalid User specified" in html or "This user has not registered" in html:
            return Result.available(url=show_url)
            
        if response.status_code == 200:
            return Result.taken(url=show_url)
            
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
        
    except Exception as e:
        return Result.error(e, url=show_url)
