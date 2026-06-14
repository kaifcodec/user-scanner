import re
import json
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_behance(user):
    url = f"https://www.behance.net/{user}/appreciated"
    show_url = f"https://www.behance.net/{user}"
    headers = {"User-Agent": get_random_user_agent()}

    try:
        response = make_request(url, headers=headers, follow_redirects=True, http2=True)
        if response.status_code == 200:
            extra = {}
            match = re.search(r'<script type="application/json" id="beconfig-store_state">({.+?})</script>', response.text)
            if match:
                try:
                    data = json.loads(match.group(1))
                    user_data = data.get('profile', {}).get('user', {})
                    if not user_data and 'user' in data.get('profile', {}):
                        user_data = data['profile']['user']
                        
                    if 'displayName' in user_data:
                        extra['fullname'] = user_data['displayName']
                    if 'location' in user_data:
                        extra['location'] = user_data['location']
                    if 'company' in user_data:
                        extra['company'] = user_data['company']
                        
                    stats = user_data.get('stats', {})
                    if 'followers' in stats:
                        extra['follower_count'] = stats['followers']
                    if 'following' in stats:
                        extra['following_count'] = stats['following']
                    if 'views' in stats:
                        extra['views_count'] = stats['views']
                except Exception:
                    pass
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
