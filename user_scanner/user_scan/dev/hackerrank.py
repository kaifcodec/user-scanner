from user_scanner.core.orchestrator import generic_validate, Result

def validate_hackerrank(user):
    url = f"https://www.hackerrank.com/rest/contests/master/hackers/{user}/profile"
    show_url = f"https://www.hackerrank.com/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                m = data.get('model', {})
                if m and m.get('id'):
                    extra = {}
                    if m.get('id'): extra['id'] = m.get('id')
                    if m.get('username'): extra['username'] = m.get('username')
                    if m.get('country'): extra['country'] = m.get('country')
                    if m.get('school'): extra['school'] = m.get('school')
                    if m.get('created_at'): extra['created_at'] = m.get('created_at')
                    if m.get('level') is not None: extra['level'] = m.get('level')
                    if m.get('company'): extra['company'] = m.get('company')
                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
