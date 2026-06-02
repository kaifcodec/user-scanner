from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request
import re


def validate_buymeacoffee(user):
    url = f"https://buymeacoffee.com/{user}"
    show_url = f"https://buymeacoffee.com/{user}"
    headers = {"User-Agent": get_random_user_agent()}

    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            extra = {}
            
            # Extract Name (from og:title or title)
            n = re.search(r'<meta property="og:title" content="([^"]+)"', response.text)
            if not n: n = re.search(r'<title[^>]*>([^<]+?)(?:\s*-\s*Buymeacoffee)?</title>', response.text, re.IGNORECASE)
            if n: extra['name'] = n.group(1).strip()
            
            m = re.search(r'<meta name="description" content="([^"]+)"', response.text)
            if not m: m = re.search(r'<meta property="og:description" content="([^"]+)"', response.text)
            if m: extra['bio'] = m.group(1).strip()
            
            img = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
            if img: extra['avatar'] = img.group(1)
            
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
