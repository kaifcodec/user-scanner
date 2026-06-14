import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_ok(user: str) -> Result:
    url = f"https://ok.ru/{user}"
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        html = response.text
        
        if response.status_code == 404 or "Этой страницы нет на OK.RU" in html or "This page does not exist on OK.RU" in html:
            return Result.available(url=url)
            
        if response.status_code == 200:
            extra = {}

            match = re.search(r'path:"/(?:profile/)?.+?",state:".+?friendId=(\d+?)"', html)
            if match:
                extra["ok_id"] = match.group(1)
            else:
                match2 = re.search(r'friendId=(\d+)', html)
                if match2:
                    extra["ok_id"] = match2.group(1)
                    
            return Result.taken(extra=extra, url=url)
            
        return Result.error(f"Unexpected status: {response.status_code}", url=url)
        
    except Exception as e:
        return Result.error(e, url=url)
