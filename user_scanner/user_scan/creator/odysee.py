import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_odysee(user: str) -> Result:
    url = f"https://odysee.com/@{user}"
    show_url = url

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        if response.status_code == 200:
            canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', response.text, re.IGNORECASE)
            if canonical_match:
                canonical_url = canonical_match.group(1)
                if "/@" in canonical_url:
                    return Result.taken(url=show_url)
                else:
                    return Result.available(url=show_url)
            
            if f"/@{user}" in response.text:
                return Result.taken(url=show_url)
            return Result.available(url=show_url)
            
        elif response.status_code == 404:
            return Result.available(url=show_url)
            
        return Result.error(f"Unexpected status code: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, http2=False, show_url=show_url)
