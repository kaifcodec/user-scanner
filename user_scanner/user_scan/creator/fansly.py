from user_scanner.core.orchestrator import generic_validate, Result

def validate_fansly(user):
    url = f"https://apiv2.fansly.com/api/v1/account?usernames={user}"
    show_url = f"https://fansly.com/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success') and data.get('response'):
                    res = data['response'][0]
                    extra = {}
                    if res.get('id'):
                        extra['id'] = res.get('id')
                    if res.get('displayName'):
                        extra['displayName'] = res.get('displayName')
                    if res.get('followCount') is not None:
                        extra['followers'] = res.get('followCount')
                    
                    timelineStats = res.get('timelineStats', {})
                    if timelineStats:
                        if timelineStats.get('imageCount') is not None:
                            extra['images'] = timelineStats.get('imageCount')
                        if timelineStats.get('videoCount') is not None:
                            extra['videos'] = timelineStats.get('videoCount')

                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
