import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request


def validate_dribbble(user):
    url = f"https://dribbble.com/{user}/about"
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
                
                name_match = re.search(r'<h1 class="masthead-profile-name">([^<]+)</h1>', html)
                bio_match = re.search(r'<p class="bio-text">([^<]+)</p>', html)
                
                loc_match = re.search(r'<p class="masthead-profile-locality"><a[^>]*>([^<]+)</a>', html)
                if not loc_match:
                    loc_match = re.search(r'class="location[^"]*">([^<]+)</span>', html, re.I)
                    
                followers_match = re.search(r'([0-9,kKmM]+)\s*</span>\s*<span class="meta">followers', html, re.I | re.DOTALL)
                following_match = re.search(r'([0-9,kKmM]+)\s*</span>\s*<span class="meta">following', html, re.I | re.DOTALL)
                member_since_match = re.search(r'Member since ([^<]+)</span>', html, re.I)

                extra = {
                    'name': name_match.group(1).strip() if name_match else None,
                    'bio': bio_match.group(1).strip() if bio_match else None,
                    'location': loc_match.group(1).strip() if loc_match else None,
                    'followers': followers_match.group(1).strip() if followers_match else None,
                    'following': following_match.group(1).strip() if following_match else None,
                    'registered': member_since_match.group(1).strip() if member_since_match else None
                }
                    
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
