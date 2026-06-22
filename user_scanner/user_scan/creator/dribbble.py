import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request


def validate_dribbble(user):
    url = f"https://dribbble.com/{user}"
    show_url = f"https://dribbble.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
    }

    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            html = response.text
            
            # Explicit verification: Dribbble normalizes casing and strips trailing slashes in its tags
            # We extract canonical or og:url and compare case-insensitively
            canonical_match = re.search(r'<link rel="canonical" href="([^"]+)"', html, re.I)
            og_match = re.search(r'<meta property="og:url" content="([^"]+)"', html, re.I)
            
            found_url = ""
            if canonical_match:
                found_url = canonical_match.group(1)
            elif og_match:
                found_url = og_match.group(1)
                
            if found_url.lower().rstrip('/') == show_url.lower().rstrip('/'):
                extra = {}
                
                meta_match = re.search(r'<meta name="description" content="([^"]+)"', html)
                if meta_match:
                    meta_content = meta_match.group(1).strip()
                    if "Find Top Designers" not in meta_content:
                        parts = [p.strip() for p in meta_content.split('|')]
                        if len(parts) > 0 and parts[0]:
                            extra['name'] = parts[0]
                        if len(parts) > 1 and parts[1]:
                            extra['bio'] = parts[1]
                    
                loc_match = re.search(r'class="location[^"]*">([^<]+)</span>', html, re.I)
                if loc_match:
                    extra['location'] = loc_match.group(1).strip()
                    
                return Result.taken(extra=extra, url=show_url)
            else:
                # Soft 404 (redirect to homepage or missing profile metadata)
                return Result.available(url=show_url)
                
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status code: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
