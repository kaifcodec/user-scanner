from user_scanner.core.orchestrator import Result, make_request
import re

def validate_xing(user: str) -> Result:
    url = f"https://www.xing.com/profile/{user}"
    show_url = url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = make_request(
            url, headers=headers, follow_redirects=True, http2=False, method="GET"
        )
        
        if response.status_code == 404:
            return Result.available(url=show_url)
            
        if response.status_code == 200:
            html = response.text
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html)
            title = title_match.group(1).strip() if title_match else ""
            
            if title == "XING":
                # Bot protection triggered, returning App Shell
                return Result.error("XING bot protection triggered (App Shell returned)", url=show_url)
            elif "404 - Not Found" in title:
                return Result.available(url=show_url)
            else:
                extra = {}
                if " | XING" in title:
                    name_part = title.split(" | XING")[0]
                    name = name_part.split(" - ")[0].strip()
                    extra["name"] = name
                return Result.taken(url=show_url, extra=extra)
                
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
