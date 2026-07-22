import re
import html
import httpx
from user_scanner.core.result import Result
from user_scanner.core import orchestrator

def validate_wix(username: str) -> Result:
    """Validate a username on Wix."""
    url = f"https://{username}.wix.com"
    show_url = f"https://{username}.wix.com"
    try:
        response = orchestrator.make_request(url, follow_redirects=True)
        response_text = response.text
        
        # Verify status code 200 AND check unique Wix strings in the response body to prevent false positives
        if response.status_code == 200 and "wix" in response_text.lower():
            extra = {}
            title_match = re.search(r"<title>(.*?)</title>", response_text, re.IGNORECASE)
            if title_match:
                extra["title"] = html.unescape(title_match.group(1).strip())
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except httpx.ConnectError:
        # If the domain doesn't resolve at all, it usually means the username/subdomain is available
        return Result.available(url=show_url)
    except httpx.TimeoutException:
        return Result.skipped("Connection timed out")
    except Exception as e:
        return Result.error(e, url=show_url)
