import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_packagist(user):
    url = f"https://packagist.org/users/{user}/"
    show_url = url
    headers = {"User-Agent": get_random_user_agent()}

    try:
        response = make_request(url, headers=headers)
        if response.status_code == 200:
            extra = {}
            # Usually username is found in the title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE)
            if title_match:
                extra['name'] = title_match.group(1).replace('- Packagist', '').strip()
                
            # Extract list of packages
            packages = re.findall(r'/packages/([^/]+/[^/"]+)', response.text)
            if packages:
                # Remove duplicates and filter
                unique_packages = list(set([p for p in packages if 'submit' not in p]))
                extra['packages_count'] = len(unique_packages)
                
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
