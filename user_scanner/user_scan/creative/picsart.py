from user_scanner.core.orchestrator import generic_validate, Result

def validate_picsart(user):
    url = f"https://api.picsart.com/users/show/{user}.json"
    show_url = f"https://picsart.com/u/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('status') == 'success':
                    extra = {}
                    if data.get('id'):
                        extra['id'] = data.get('id')
                    if data.get('name'):
                        extra['name'] = data.get('name')
                    if data.get('status_message'):
                        extra['status_message'] = data.get('status_message')
                    if data.get('followers_count') is not None:
                        extra['followers'] = data.get('followers_count')
                    if data.get('following_count') is not None:
                        extra['following'] = data.get('following_count')
                    if data.get('likes_count') is not None:
                        extra['likes'] = data.get('likes_count')
                    if data.get('photos_count') is not None:
                        extra['photos'] = data.get('photos_count')

                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
