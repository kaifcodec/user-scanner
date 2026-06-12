from user_scanner.core.orchestrator import generic_validate, Result

def validate_boosty(user):
    url = f"https://api.boosty.to/v1/blog/{user}"
    show_url = f"https://boosty.to/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('owner'):
                    extra = {}
                    
                    owner = data.get('owner', {})
                    if owner.get('id'):
                        extra['id'] = owner.get('id')
                    if owner.get('name'):
                        extra['name'] = owner.get('name')
                        
                    count = data.get('count', {})
                    if count.get('subscribers') is not None:
                        extra['subscribers'] = count.get('subscribers')
                    if count.get('posts') is not None:
                        extra['posts'] = count.get('posts')
                        
                    if data.get('title'):
                        extra['title'] = data.get('title')
                        
                    apps = owner.get('externalApps', {})
                    if apps.get('discord', {}).get('hasAccount'):
                        extra['has_discord'] = True
                    if apps.get('telegram', {}).get('hasAccount'):
                        extra['has_telegram'] = True

                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
