import re
import json
from user_scanner.core.orchestrator import generic_validate, Result

def validate_habr(user):
    url = f"https://habr.com/ru/users/{user}/"
    show_url = url

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            match = re.search(r'\"authorRefs\":(\{.*?\})(?=,\"authorIds\")', response.text)
            if match:
                text = match.group(1).replace('undefined', 'null')
                try:
                    data = json.loads(text)
                    user_key = next((k for k in data.keys() if k != '__ALIAS_STORE__'), None)
                    if user_key:
                        user_info = data[user_key]
                        extra = {}
                        if user_info.get('fullname'): extra['name'] = user_info.get('fullname')
                        if user_info.get('speciality'): extra['speciality'] = user_info.get('speciality')
                        if user_info.get('rating') is not None: extra['rating'] = user_info.get('rating')
                        if user_info.get('scoreStats', {}).get('score') is not None: extra['karma'] = user_info.get('scoreStats', {}).get('score')
                        if user_info.get('followStats', {}).get('followersCount') is not None: extra['followers'] = user_info.get('followStats', {}).get('followersCount')
                        if user_info.get('followStats', {}).get('followCount') is not None: extra['following'] = user_info.get('followStats', {}).get('followCount')
                        if user_info.get('counterStats', {}).get('postCount') is not None: extra['posts'] = user_info.get('counterStats', {}).get('postCount')
                        if user_info.get('counterStats', {}).get('commentCount') is not None: extra['comments'] = user_info.get('counterStats', {}).get('commentCount')
                        if user_info.get('registerDateTime'): extra['registered'] = user_info.get('registerDateTime')
                        if user_info.get('avatarUrl'): extra['avatar'] = user_info.get('avatarUrl')
                        return Result.taken(extra=extra)
                except Exception:
                    pass
        return Result.error(f"Unexpected response status: {response.status_code}")

    headers = {"User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
