import re
from user_scanner.core.orchestrator import Result, make_request

def validate_figma(user):
    show_url = f"https://www.figma.com/@{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    try:
        response = make_request(show_url, headers=headers, follow_redirects=True)
        
        if response.status_code == 200:
            html = response.text
            extra = {}
            
            # Extract name from twitter:title if possible
            match = re.search(r'<meta\s+property="twitter:title"\s+content="([^"]+)"', html)
            if match:
                title_content = match.group(1)
                # Parse out "Name (@username)" format
                if "(@" in title_content:
                    name = title_content.split("(@")[0].strip()
                    extra["name"] = name
                else:
                    extra["name"] = title_content
            
            return Result.taken(url=show_url, extra=extra)
            
        elif response.status_code in [404, 202]:
            return Result.available(url=show_url)
            
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
            
    except Exception as e:
        return Result.error(e, url=show_url)
