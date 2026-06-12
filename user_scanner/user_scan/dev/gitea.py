from user_scanner.core.orchestrator import generic_validate, Result

def validate_gitea(user):
    url = f"https://gitea.com/api/v1/users/{user}"
    show_url = f"https://gitea.com/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data and data.get('id'):
                    extra = {}
                    if data.get('id'): extra['id'] = data.get('id')
                    if data.get('login'): extra['login'] = data.get('login')
                    if data.get('full_name'): extra['full_name'] = data.get('full_name')
                    if data.get('email'): extra['email'] = data.get('email')
                    if data.get('created'): extra['created'] = data.get('created')
                    if data.get('location'): extra['location'] = data.get('location')
                    if data.get('website'): extra['website'] = data.get('website')
                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
