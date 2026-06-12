from user_scanner.core.orchestrator import generic_validate, Result

def validate_pr0gramm(user):
    url = f"https://pr0gramm.com/api/profile/info?name={user}"
    show_url = f"https://pr0gramm.com/user/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                u = data.get('user', {})
                if u and u.get('id'):
                    extra = {}
                    if u.get('id'): extra['id'] = u.get('id')
                    if u.get('name'): extra['name'] = u.get('name')
                    if u.get('registered'): extra['registered'] = u.get('registered')
                    if u.get('score') is not None: extra['score'] = u.get('score')
                    if u.get('mark') is not None: extra['mark'] = u.get('mark')
                    if data.get('commentCount') is not None: extra['comments'] = data.get('commentCount')
                    if data.get('uploadCount') is not None: extra['uploads'] = data.get('uploadCount')
                    if data.get('tagCount') is not None: extra['tags'] = data.get('tagCount')
                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
