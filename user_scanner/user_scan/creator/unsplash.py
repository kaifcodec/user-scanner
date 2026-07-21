import re
import html
import httpx
from user_scanner.core.result import Result
from user_scanner.core.orchestrator import make_request

def validate_unsplash(username: str) -> Result:
    """Validate a username on Unsplash."""
    url = f"https://unsplash.com/@{username}"
    show_url = f"https://unsplash.com/@{username}"
    
    try:
        # We pass headers={} to use httpx's default user-agent, 
        # as Unsplash blocks/redirects the default browser user-agent.
        response = make_request(url, headers={}, follow_redirects=True)
        response_text = response.text
        
        # Verify status code 200 AND check unique Unsplash strings in the response body to prevent false positives
        if response.status_code == 200 and "unsplash" in response_text.lower() and "page not found" not in response_text.lower():
            extra = {}
            title_match = re.search(r"<title>(.*?)</title>", response_text, re.IGNORECASE)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
                title_clean = title.split(" | ")[0]
                match = re.search(r"^(.*?)\s*\((?:@" + re.escape(username) + r")\)", title_clean, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    name = re.sub(r"'\s*s (?:Collections|Photos|Likes|Stats)$", "", name, flags=re.IGNORECASE)
                    name = re.sub(r"'\''s (?:Collections|Photos|Likes|Stats)$", "", name, flags=re.IGNORECASE)
                    extra["name"] = name
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404 or "page not found" in response_text.lower():
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except httpx.TimeoutException:
        return Result.skipped("Connection timed out")
    except Exception as e:
        return Result.error(e, url=show_url)
