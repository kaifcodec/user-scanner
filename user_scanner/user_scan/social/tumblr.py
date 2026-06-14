import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_tumblr(user):
    url = f"https://{user}.tumblr.com/"
    show_url = url
    headers = {"User-Agent": get_random_user_agent()}

    try:
        response = make_request(url, headers=headers)
        if response.status_code == 200:
            extra = {}
            title = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE)
            if title:
                extra["title"] = title.group(1).strip()
            
            desc = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', response.text, re.IGNORECASE)
            if not desc:
                desc = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', response.text, re.IGNORECASE)
            if desc:
                extra["description"] = desc.group(1).strip()
                
            img = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', response.text, re.IGNORECASE)
            if img:
                extra["avatar"] = img.group(1).strip()
                
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
