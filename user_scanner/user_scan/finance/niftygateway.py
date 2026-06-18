from user_scanner.core.orchestrator import generic_validate, Result

def validate_niftygateway(user):
    url = f"https://api.niftygateway.com/user/profile-and-offchain-nifties-by-url/?profile_url={user}"
    show_url = f"https://niftygateway.com/profile/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('didSucceed'):
                    user_info = data.get('userProfileAndNifties', {})
                    if user_info and user_info.get('id'):
                        extra = {}
                        if user_info.get('id'):
                            extra['id'] = user_info.get('id')
                        if user_info.get('user_id'):
                            extra['user_id'] = user_info.get('user_id')
                        if user_info.get('name'):
                            extra['name'] = user_info.get('name')
                        if user_info.get('bio'):
                            extra['bio'] = user_info.get('bio')
                        
                        return Result.taken(extra=extra)
                    else:
                        return Result.available()
            except Exception:
                pass
        elif response.status_code in (404, 400) or 'not_found' in response.text:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
