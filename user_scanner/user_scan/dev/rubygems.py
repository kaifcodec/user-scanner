import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_rubygems(user):
    url = f"https://rubygems.org/profiles/{user}"
    show_url = url
    headers = {"User-Agent": get_random_user_agent()}

    try:
        response = make_request(url, headers=headers)
        if response.status_code == 200:
            extra = {}
            # Try to extract the user's name from title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE)
            if title_match:
                # E.g. "Profile of alex | RubyGems.org"
                name = title_match.group(1).split('|')[0].replace('Profile of', '').strip()
                if name:
                    extra['name'] = name
                    
            # Try to extract the gems count if available
            gems_match = re.search(r'Gems\s*<span[^>]*>(\d+)</span>', response.text, re.IGNORECASE)
            if gems_match:
                extra['gems_count'] = int(gems_match.group(1))
                
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
