from user_scanner.core.orchestrator import generic_validate, Result

def validate_duolingo(user):
    url = f"https://www.duolingo.com/2017-06-30/users?username={user}"
    show_url = f"https://www.duolingo.com/profile/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                users = data.get('users', [])
                if users:
                    u = users[0]
                    extra = {}
                    if u.get('id'): extra['id'] = u.get('id')
                    if u.get('name'): extra['name'] = u.get('name')
                    if u.get('creationDate'): extra['created'] = u.get('creationDate')
                    if u.get('totalXp') is not None: extra['total_xp'] = u.get('totalXp')
                    if u.get('streak') is not None: extra['streak'] = u.get('streak')
                    if u.get('hasPlus'): extra['has_plus'] = u.get('hasPlus')
                    
                    courses = u.get('courses', [])
                    if courses:
                        extra['courses'] = len(courses)
                    return Result.taken(extra=extra)
                else:
                    return Result.available()
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
