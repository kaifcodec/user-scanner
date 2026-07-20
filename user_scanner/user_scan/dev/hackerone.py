import re
import html
import httpx
from user_scanner.core.result import Result
from user_scanner.core import orchestrator

def validate_hackerone(username: str) -> Result:
    """Validate a username on HackerOne."""
    url = f"https://hackerone.com/{username}"
    show_url = f"https://hackerone.com/{username}"
    try:
        response = orchestrator.make_request(url, follow_redirects=True)
        response_text = response.text
        
        # Verify status code 200 AND check unique HackerOne strings in the response body to prevent false positives
        if response.status_code == 200 and "hackerone" in response_text.lower() and f"hackerone.com/{username}" in response_text.lower():
            extra = {}
            # Extract user bio/description from OpenGraph metadata
            bio_match = re.search(r'property="og:description"\s+content="([^"]+)"', response_text, re.IGNORECASE)
            if not bio_match:
                bio_match = re.search(r'content="([^"]+)"\s+property="og:description"', response_text, re.IGNORECASE)
            if bio_match:
                bio = html.unescape(bio_match.group(1).strip())
                if bio and bio != "-":
                    extra["bio"] = bio
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404 or "page not found" in response_text.lower():
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except httpx.TimeoutException:
        return Result.skipped("Connection timed out")
    except Exception as e:
        return Result.error(e, url=show_url)
