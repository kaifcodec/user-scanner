from user_scanner.core.orchestrator import generic_validate, Result

def validate_imgur(user):
    url = f"https://api.imgur.com/account/v1/accounts/{user}?client_id=546c25a59c58ad7&include=trophies%2Cmedallions"
    show_url = f"https://imgur.com/user/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('id'):
                    extra = {}
                    if data.get('id'):
                        extra['id'] = data.get('id')
                    if data.get('bio'):
                        extra['bio'] = data.get('bio')
                    if data.get('reputation_count') is not None:
                        extra['reputation'] = data.get('reputation_count')
                    if data.get('reputation_name'):
                        extra['reputation_name'] = data.get('reputation_name')
                    if data.get('created_at'):
                        extra['created_at'] = data.get('created_at')
                    
                    trophies = data.get('trophies', [])
                    if trophies:
                        extra['trophies'] = ", ".join(t.get('name', '') for t in trophies if t.get('name'))
                        
                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404 or response.status_code == 400:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
