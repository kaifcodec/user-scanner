import re
import json
from user_scanner.core.orchestrator import Result, make_request


def validate_producthunt(user: str) -> Result:
    if not (2 <= len(user) <= 32):
        return Result.error("Length must be 2-32 characters.")

    # Rules: Letters, numbers, and underscores only.
    if not re.match(r"^[a-zA-Z0-9_]+$", user):
        return Result.error("Only use letters, numbers, and underscores.")

    url = f"https://www.producthunt.com/@{user}"
    show_url = f"https://www.producthunt.com/@{user}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            html = response.text
            extra = {}
            
            ld = re.search(r'<script type=\"application/ld\+json\">(.*?)</script>', html, re.DOTALL)
            if ld:
                try:
                    data = json.loads(ld.group(1))
                    if isinstance(data, list): data = data[0]
                    if name := data.get("name"): extra["name"] = name
                    if curl := data.get("url"): extra["url"] = curl
                except:
                    pass
                    
            if "name" not in extra:
                title_match = re.search(r'<title>([^<]+?)(?:&#x27;s|\'s) profile', html)
                if title_match:
                    extra["name"] = title_match.group(1).strip()
                else:
                    meta = re.search(r'See what kind of products\s+([^\(]+)', html)
                    if meta:
                        extra["name"] = meta.group(1).strip()
                        
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
