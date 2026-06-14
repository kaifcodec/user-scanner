from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_themeforest(user: str) -> Result:
    url = f"https://themeforest.net/user/{user}"
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        
        if response.status_code == 200:
            return Result.taken(url=url)
        elif response.status_code == 404:
            return Result.available(url=url)
            
        return Result.error(f"Unexpected response status: {response.status_code}", url=url)
        
    except Exception as e:
        return Result.error(e, url=url)
