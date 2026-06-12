from user_scanner.core.orchestrator import generic_validate, Result

def validate_gitee(user):
    url = f"https://gitee.com/api/v5/users/{user}"
    show_url = f"https://gitee.com/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data and data.get('id'):
                    extra = {}
                    if data.get('id'): extra['id'] = data.get('id')
                    if data.get('login'): extra['login'] = data.get('login')
                    if data.get('name'): extra['name'] = data.get('name')
                    if data.get('bio'): extra['bio'] = data.get('bio')
                    if data.get('blog'): extra['blog'] = data.get('blog')
                    if data.get('public_repos') is not None: extra['public_repos'] = data.get('public_repos')
                    if data.get('followers') is not None: extra['followers'] = data.get('followers')
                    if data.get('following') is not None: extra['following'] = data.get('following')
                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
